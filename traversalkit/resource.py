import weakref
from itertools import chain
from contextlib import contextmanager
from warnings import warn

from cached_property import cached_property

from .route import Node, Route
from .cache import Cache


class ResourceMeta(type):
    """ Resource metaclass """

    def __init__(cls, class_name, bases, attrs):
        cls._children_map = {}
        cls._children_set = []
        cls._named_nodes = {}
        cls.__not_exist__ = getattr(cls, '__not_exist__', None)


# For compatibility between Python 2.x and Python 3.x
BaseResource = ResourceMeta('BaseResource', (object,), {})


class Resource(BaseResource):
    """
    Base class of resource.

    ..  attribute:: __nodeclass__

        Class of route nodes.  Links to :class:`traversalkit.route.Node`.

    ..  attribute:: __routeclass__

        Class of route.  Links to :class:`traversalkit.route.Route`.

    ..  attribute:: __cacheclass__

        Class of cache.  Links to :class:`traversalkit.cache.Cache`.

    ..  attribute:: __not_exist__

        Exception class or list of ones, that should be treated as a signal
        that resource does not exist.

        These exceptions will be replaced by ``KeyError`` within methods
        :meth:`__getitem__`, :meth:`get`, and :meth:`node`.

        ..  doctest::

                >>> import re
                >>> from traversalkit import Resource

                >>> class Files(Resource):
                ...     ''' Files collection '''

                >>> @Files.mount_set(re.compile(r'^[\w\d\.\_]+$'),
                ...                  metaname='filename')
                ... class File(Resource):
                ...     ''' File resource '''
                ...     __not_exist__ = IOError
                ...     #               ^^^^^^^
                ...     def on_init(self, payload):
                ...         with open(self.__name__) as f:
                ...             self.content = f.read()

                >>> files = Files()
                >>> files['nonexistent_file.txt']  # DOCTEST: +ellipsis
                Traceback (most recent call last):
                ...
                KeyError: ('nonexistent_file.txt', '/')

    ..  attribute:: __name__

        Resource name, which has been passed to parent's :meth:`__getitem__` or
        :meth:`get` method.

    ..  attribute:: __parent__

        Link to a parent resource.  It is actually a property, which
        stores weak reference to the parent.

    ..  attribute:: __cache__

        Cache of child resources.  It is used by :meth:`__getitem__` and
        :meth:`get` methods.  Instance of :attr:`__cacheclass__`.

    ..  attribute:: __node__

        Route node, which has been used to create this resource.
        Instance of :attr:`__nodeclass__`.

    ..  attribute:: __route__

        Route, which has been used to create this resource.
        Instance of :attr:`__routeclass__`.

    ..  attribute:: uri

        URI of the resource.


    """

    __nodeclass__ = Node
    __routeclass__ = Route
    __cacheclass__ = Cache

    ##
    # Resource tree manipulation and introspection
    #

    @classmethod
    def mount(cls, name, class_=None, complies=None, **kw):
        """
        Mounts single named child resource.

        :param str name: Name of the child resource.
        :param Resource class_: Child resource class.
        :param Condition complies: Condition of the route.
            See examples of :class:`traversalkit.condition.Under`
            and :class:`traversalkit.condition.Recursion` for details.
        :return: Unmodified ``class_``.

        The method can be used as a decorator.

        ..  doctest::

            >>> from traversalkit import Resource

            >>> class Root(Resource):
            ...     ''' Site root '''

            >>> @Root.mount('users')
            ... class Users(Resource):
            ...     ''' Collection of users '''

            >>> root = Root()
            >>> root['users']
            <Users: /users/>

        """
        def decorator(class_):
            node = cls.__nodeclass__(class_,
                                     name=name,
                                     complies=complies,
                                     **kw)
            cls._children_map[name] = node
            cls._named_nodes[name] = node
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    @classmethod
    def mount_set(cls,
                  pattern,
                  class_=None,
                  metaname=None,
                  complies=None,
                  **kw):
        """
        Mounts set of child resources.

        :param regex pattern: Regular expression to match child name.
        :param Resource class_: Child resource class.
        :param str metaname: Name of the route.  It is used by :meth:`node`.
        :param Condition complies: Condition of the route.
            See examples of :class:`traversalkit.condition.Under`
            and :class:`traversalkit.condition.Recursion` for details.
        :return: Unmodified ``class_``.

        The method can be used as a decorator.

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Users(Resource):
            ...     ''' Collection of users '''

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''

            >>> users = Users()
            >>> users['1']
            <User: /1/>
            >>> users['john']  # DOCTEST: +ellipsis
            Traceback (most recent call last):
            ...
            KeyError: ('john', '/')

        """
        def decorator(class_):
            node = cls.__nodeclass__(class_,
                                     pattern=pattern,
                                     metaname=metaname,
                                     complies=complies,
                                     **kw)
            cls._children_set.append(node)
            if node.metaname is not None:
                cls._named_nodes[node.metaname] = node
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    @classmethod
    def routes(cls):
        """
        Iterates over all routes available at the current resource.

        The method is useful for resource tree introspection and documentation.

        :return: Iterator over available routes,
                 see :class:`traversalkit.route.Route`.

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Root(Resource):
            ...     ''' Site root '''

            >>> @Root.mount('users')
            ... class Users(Resource):
            ...     ''' Collection of users '''

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''

            >>> for route in Root.routes():
            ...     print(route)
            <Route: />
            <Route: /users/>
            <Route: /users/{user_id}/>

        """
        def walktree(class_, route):
            yield route

            single_nodes = (class_._children_map[name]
                            for name in sorted(class_._children_map.keys()))
            set_nodes = (node for node in class_._children_set)

            for node in chain(single_nodes, set_nodes):
                if node.complies(route):
                    for sub_route in walktree(node.class_, route + node):
                        yield sub_route

        start_route = cls.__routeclass__(cls.__nodeclass__(cls, name=''))
        for route in walktree(cls, start_route):
            yield route

    ##
    # Initialization methods and properties
    #

    def __init__(self, name='', parent=None, payload=None, node=None):
        self.__name__ = name
        self.__parent__ = parent
        self.__cache__ = self.__cacheclass__()
        self.__node__ = node or self.__nodeclass__(self.__class__, name=name)
        self.on_init(payload)

    def on_init(self, payload):
        """
        Initialization callback.

        Derived classes should override this method instead of
        :meth:`__init__`.

        :param payload: Some additional data, that can be passed into
                        initialization routine through :meth:`get`
                        or :meth:`node`.  If resource is created
                        by :meth:`__getitem__`, the parameter will be ``None``.

        """

    @property
    def __parent__(self):
        return self.__parent()

    @__parent__.setter
    def __parent__(self, parent):
        self.__parent = weakref.ref(parent) if parent else lambda: None

    @cached_property
    def __route__(self):
        if self.__parent__ is None:
            return self.__routeclass__(self.__node__)
        return self.__parent__.__route__ + self.__node__

    @cached_property
    def uri(self):
        path = [r.__name__ for r in self.lineage()]
        path.reverse()
        path.append('')
        return '/'.join(path)

    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__, self.uri)

    ##
    # Child creation methods
    #

    @contextmanager
    def node(self, name):
        """
        Returns context manager of named route node.

        :param string name: Name of the route node, i.e. ``name`` parameter
                            of :meth:`mount` or ``metaname`` parameter
                            of :meth:`mount_set`.
        :raises KeyError: If node does not exist or current route does not
                          comply condition.

        The context manager can be used to create multiple child resources,
        passing route validation only once.  It has the following signature:

        ..  code-block:: python

            def create_child(name, payload=None):

        :param string name: Name of the resource.
        :param payload: Optional resource payload.
        :return: Child resource.
        :rtype: Resource

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Users(Resource):
            ...     ''' Collection of users '''
            ...     def index(self):
            ...         # Let's imagine these data come from DB
            ...         # and there is a lot of records.
            ...         users = [{'id': 1, 'name': 'Jonh'},
            ...                  {'id': 2, 'name': 'Jane'}]
            ...         with self.node('user_id') as create_child:
            ...         #    ^^^^^^^^^^^^^^^^^^^^
            ...         #    here we pass route validation
            ...             for user in users:
            ...                 yield create_child(str(user['id']), user)
            ...                 #     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            ...                 #     and here create multiple resources

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''
            ...     def on_init(self, payload):
            ...         if payload is not None:
            ...             self.id = payload['id']
            ...             self.name = payload['name']

            >>> users = Users()
            >>> john, jane = users.index()
            >>> john.name
            'Jonh'
            >>> jane.name
            'Jane'
            >>> users['1'] is john
            True
            >>> users['2'] is jane
            True

        """
        try:
            node = self._named_nodes[name]
        except KeyError:
            raise KeyError(name, self.uri)
        if not node.complies(self.__route__):
            raise KeyError(name, self.uri)

        def create_child(name, payload=None):
            return self._child(node, name, payload=payload)

        yield create_child

    def __getitem__(self, name):
        """
        Returns child resource by its name.

        Child resource class should be mounted using :meth:`mount` or
        :meth:`mount_set` methods.

        The method uses cache.  Therefore it won't create child resource,
        if it's already created.

        :param str name: Resource name.
        :return: Child resource.
        :rtype: Resource
        :raises KeyError: If name does not match any route,
                          or current route does not comply condition.

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Root(Resource):
            ...     ''' Site root '''

            >>> @Root.mount('users')
            ... class Users(Resource):
            ...     ''' Collection of users '''

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''

            >>> root = Root()
            >>> root['users']
            <Users: /users/>
            >>> root['users']['1']
            <User: /users/1/>

        """
        return self.get(name)

    def get(self, name, payload=None):
        """
        Returns child resource by its name.

        Child resource class should be mounted using :meth:`mount` or
        :meth:`mount_set` methods.

        The method uses cache.  Therefore it won't create child resource,
        if it's already created.

        :param str name: Resource name.
        :param payload: Optional resource payload.
        :return: Child resource.
        :rtype: Resource
        :raises KeyError: If name does not match any route,
                          or current route does not comply condition.

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Root(Resource):
            ...     ''' Site root '''

            >>> @Root.mount('users')
            ... class Users(Resource):
            ...     ''' Collection of users '''

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''
            ...     def on_init(self, payload):
            ...         if payload is not None:
            ...             self.id = payload['id']
            ...             self.name = payload['name']

            >>> root = Root()
            >>> root['users']
            <Users: /users/>
            >>> user = root['users'].get('1', {'id': 1, 'name': 'John'})
            >>> user
            <User: /users/1/>
            >>> user.name
            'John'
            >>> user.id
            1

        """
        try:
            return self.__cache__[name]
        except KeyError:
            pass
        try:
            node = self._children_map[name]
        except KeyError:
            for node in self._children_set:
                if node.pattern.match(name):
                    break
            else:
                raise KeyError(name, self.uri)
        if not node.complies(self.__route__):
            raise KeyError(name, self.uri)
        return self._child(node, name, payload=payload)

    def _child(self, node, name, payload=None):
        try:
            child = self.__cache__[name] = node.class_(
                name=name,
                parent=self,
                payload=payload,
                node=node,
            )
        except Exception as e:
            if node.class_.__not_exist__ and \
               isinstance(e, node.class_.__not_exist__):
                raise KeyError(name, self.uri)
            raise
        return child

    ##
    # Lineage introspection methods
    #

    def lineage(self):
        """
        Returns iterator over resource parents.

        Lineage chain includes current resource.

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Root(Resource):
            ...     ''' Site root '''

            >>> @Root.mount('users')
            ... class Users(Resource):
            ...     ''' Collection of users '''

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''

            >>> root = Root()
            >>> list(root['users']['1'].lineage())
            [<User: /users/1/>, <Users: /users/>, <Root: />]

        """
        resource = self
        while resource:
            yield resource
            resource = resource.__parent__

    def parent(self, name=None, cls=None):
        """
        Searches particular parent in the resource lineage.

        :param str name: Optional parent name.
        :param Resource,str cls: Optional class or class name of parent.
        :return: Parent resource or ``None``.

        ..  doctest::

            >>> from traversalkit import Resource, DEC_ID

            >>> class Root(Resource):
            ...     ''' Site root '''

            >>> @Root.mount('users')
            ... class Users(Resource):
            ...     ''' Collection of users '''

            >>> @Users.mount_set(DEC_ID, metaname='user_id')
            ... class User(Resource):
            ...     ''' User resource '''

            >>> root = Root()
            >>> user = root['users']['1']
            >>> user.parent('users')
            <Users: /users/>
            >>> user.parent(cls='Root')
            <Root: />
            >>> user.parent(cls=Root)
            <Root: />
            >>> user.parent()
            <Users: /users/>

        """
        if name is not None:
            def check(resource):
                return resource.__name__ == name
        elif cls is not None:
            if isinstance(cls, type):
                def check(resource):
                    return resource.__class__ is cls
            else:
                def check(resource):
                    return resource.__class__.__name__ == cls
        else:
            return self.__parent__
        for resource in self.lineage():
            if check(resource):
                return resource
        return None

    ##
    # Deprecated methods
    #

    def child(self, class_, name, payload=None):
        """
        ..  warning:: Deprecated in favor of :meth:`node`.

        Creates child resource from given class and name.

        """
        warn('Method ``child`` is deprected '
             'in favor of ``node`` context manager',
             DeprecationWarning)
        node = self.__nodeclass__(class_, name=name)
        return self._child(node, name, payload=payload)
