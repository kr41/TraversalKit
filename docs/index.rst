TraversalKit
============

The library provides tools to build resource tree for applications that use
traversal routing.  It has been developed to be used with Pyramid_ web
application framework, however it does not depend on it and can be used
within any application.

It helps implement resource tree hierarchy in a simple declarative way:

..  _Pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/

..  doctest::

    >>> from traversalkit import Resource, DEC_ID

    >>> class Root(Resource):
    ...     """ Tree root """

    >>> @Root.mount('users')
    ... class Users(Resource):
    ...     """ Users collection """

    >>> @Users.mount_set(DEC_ID, metaname='user_id')
    ... class User(Resource):
    ...     """ User resource """

    >>> @Root.mount('posts')
    ... @User.mount('posts')
    ... class Posts(Resource):
    ...     """ Posts collection """

    >>> @Posts.mount_set(DEC_ID, metaname='post_id')
    ... class Post(Resource):
    ...     """ Post resource """

    >>> for route in Root.routes():
    ...     print(route)
    <Route: />
    <Route: /posts/>
    <Route: /posts/{post_id}/>
    <Route: /users/>
    <Route: /users/{user_id}/>
    <Route: /users/{user_id}/posts/>
    <Route: /users/{user_id}/posts/{post_id}/>

These resources comply `Pyramid traversal`_ interface and
`Pyramid location awareness`_ interface.

..  _Pyramid traversal: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html
..  _Pyramid location awareness: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/resources.html#location-aware-resources

..  doctest::

    >>> root = Root()
    >>> user = root['users']['1']
    >>> user
    <User: /users/1/>
    >>> user.__name__
    '1'
    >>> user.__parent__
    <Users: /users/>
    >>> user['posts']
    <Posts: /users/1/posts/>
    >>> user['documents']  # DOCTEST: +ellipsis
    Traceback (most recent call last):
    ...
    KeyError: ('documents', '/users/1/')


..  toctree::
    :maxdepth: 2
    :caption: Contents:

    changes
    internals/index



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
