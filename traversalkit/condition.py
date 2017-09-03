"""
The module provides condition descriptors of routes.

"""

# For compatibility between Python 2.x and Python 3.x
try:  # pragma: no cover
    string = basestring
except NameError:  # pragma: no cover
    string = str


class Condition(object):
    """
    Base class for condition.

    The class provides implementation of some syntactic sugar:

    ..  doctest::

        >>> Condition() & Condition()
        And(Condition(), Condition())

        >>> Condition() | Condition()
        Or(Condition(), Condition())

        >>> ~Condition()
        Not(Condition())

    Derived class should only override :meth:`__call__` method.

    """

    def __call__(self, route):  # pragma: no cover
        """
        Test route against the condition.

        :param Route route: Route to test.
        :return: The result of test, i.e. ``True`` if given route complies
                 the condition, or ``False`` otherwise.
        :rtype: bool
        :raises NotImplementedError: If not overridden.

        """
        raise NotImplementedError('The method should be overridden')

    def __invert__(self):
        return Not(self)

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __repr__(self):
        params = (
            '%s=%r' % (key, value)
            for key, value in self.__dict__.items()
        )
        params = ', '.join(params)
        return '%s(%s)' % (self.__class__.__name__, params)


class Not(Condition):
    """
    Utility class to negate wrapped condition.

    It does not have to be used directly.  Use ``~`` operator instead:

    ..  doctest::

        >>> ~Condition()
        Not(Condition())

    :param Condition condition: Condition to negate.

    """

    def __init__(self, condition):
        self.condition = condition

    def __call__(self, route):
        return not self.condition(route)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.condition)


class And(Condition):
    """
    Utility class to concatenate wrapped conditions by logical ``AND``.

    It does not have to be used directly.  Use ``&`` operator instead:

    ..  doctest::

        >>> Condition() & Condition()
        And(Condition(), Condition())

    :param Condition left: Left condition.
    :param Condition right: Right condition.

    """

    def __init__(self, left, rigth):
        self.left = left
        self.rigth = rigth

    def __call__(self, route):
        return self.left(route) and self.rigth(route)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.left, self.rigth)


class Or(Condition):
    """
    Utility class to concatenate wrapped conditions by logical ``OR``.

    It does not have to be used directly.  Use ``|`` operator instead:

    ..  doctest::

        >>> Condition() | Condition()
        Or(Condition(), Condition())

    :param Condition left: Left condition.
    :param Condition right: Right condition.

    """

    def __init__(self, left, rigth):
        self.left = left
        self.rigth = rigth

    def __call__(self, route):
        return self.left(route) or self.rigth(route)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.left, self.rigth)


class Under(Condition):
    """
    Test that route contains specified parents.

    :param Resource,str *parents: List of resource classes or resource names.

    The following example describes simple blog with two sections of posts:
    published ones and drafts.  Published post can contain comments section,
    but draft cannot.  This restriction is done using :class:`Under` condition
    negated by :class:`Not` (i.e. ``~`` operator).

    ..  doctest::

        >>> from traversalkit import Resource, DEC_ID

        >>> class Blog(Resource):
        ...     ''' Blog root resource '''

        >>> @Blog.mount('posts')   # Published posts can contain comments
        ... @Blog.mount('drafts')  # Draft posts cannot contain comments
        ... class Posts(Resource):
        ...     ''' Blog posts collection '''

        >>> @Posts.mount_set(DEC_ID, metaname='post_id')
        ... class Post(Resource):
        ...     ''' Blog post '''

        >>> @Post.mount('comments', complies=~Under('drafts'))
        ... class Comments(Resource):  #     ^^^^^^^^^^^^^^^^
        ...     ''' Comments collection '''

        >>> blog = Blog()
        >>> blog['posts']['1']['comments']
        <Comments: /posts/1/comments/>

        >>> blog['drafts']['2']['comments']  # DOCTEST: +ellipsis
        Traceback (most recent call last):
        ...
        KeyError: ('comments', '/drafts/2/')

        >>> for route in Blog.routes():
        ...     print(route)
        <Route: />
        <Route: /drafts/>
        <Route: /drafts/{post_id}/>
        <Route: /posts/>
        <Route: /posts/{post_id}/>
        <Route: /posts/{post_id}/comments/>

    """

    def __init__(self, *parents):
        self.parents = parents

    def __call__(self, route):
        for node in route:
            if node.class_ in self.parents:
                return True
            if node.name is not None and node.name in self.parents:
                return True
        return False

    def __repr__(self):
        parents = (repr(p) for p in self.parents)
        parents = ', '.join(parents)
        return '%s(%s)' % (self.__class__.__name__, parents)


class Recursion(Condition):
    """
    Test that route does not go deeper than specified recursion depth.

    :param int maxdepth: Maximum recursion depth.

    The following example describes categories tree.  Where collection resource
    ``Categories`` contains item resource ``Category``, which again contains
    collection ``Categories``.  To restrict this endless route
    :class:`Recursion` condition is used with maximum depth of 2.

    ..  doctest::

        >>> from traversalkit import Resource, DEC_ID

        >>> class Categories(Resource):
        ...     ''' Categories collection '''

        >>> @Categories.mount_set(DEC_ID, metaname='category_id')
        ... class Category(Resource):
        ...     ''' Category resource '''

        >>> Category.mount(
        ...     'categories', Categories,
        ...     complies=Recursion(maxdepth=2),
        ...     #        ^^^^^^^^^^^^^^^^^^^^^
        ... )   # DOCTEST: +ellipsis
        <class ...

        >>> tree = Categories()
        >>> tree['1']['categories']['2']
        <Category: /1/categories/2/>

        >>> tree['1']['categories']['2']['categories']  # DOCTEST: +ellipsis
        Traceback (most recent call last):
        ...
        KeyError: ('categories', '/1/categories/2/')

        >>> for route in Categories.routes():
        ...     print(route)
        <Route: />
        <Route: /{category_id}/>
        <Route: /{category_id}/categories/>
        <Route: /{category_id}/categories/{category_id}/>

    """

    def __init__(self, maxdepth):
        self.maxdepth = maxdepth

    def __call__(self, route):
        depth = 0
        target = route[-1]
        for node in route:
            if node.class_ is target.class_:
                depth += 1
        return self.maxdepth >= depth
