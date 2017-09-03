from collections import MutableMapping
from contextlib import contextmanager


class Cache(MutableMapping):
    """
    Resource cache.

    Provides regular mutable mapping interface with additional ``readonly``
    method.  The ``readonly`` returns a context manager, that can be used to
    temporary freeze cache state.

    ..  doctest::

        >>> cache = Cache()
        >>> cache['x'] = 1
        >>> cache['y'] = 2
        >>> cache == {'x': 1, 'y': 2}
        True

        >>> with cache.readonly():
        ...     cache['x'] = 3
        ...     del cache['y']

        >>> cache == {'x': 1, 'y': 2}
        True

    It is useful when you do not want to cache child resources:

    ..  doctest::

        >>> from traversalkit import Resource, DEC_ID

        >>> class Users(Resource):
        ...     ''' Collection of users '''

        >>> @Users.mount_set(DEC_ID, metaname='user_id')
        ... class User(Resource):
        ...     ''' User resource '''

        >>> users = Users()
        >>> with users.__cache__.readonly():
        ...     user_1 = users['1']

        >>> user_2 = users['2']
        >>> users['2'] is user_2
        True
        >>> users['1'] is user_1
        False

    """

    def __init__(self, *args, **kw):
        self._payload = {}
        self._readonly = False
        self.update(*args, **kw)

    def __getitem__(self, key):
        return self._payload[key]

    def __setitem__(self, key, value):
        if not self._readonly:
            self._payload[key] = value

    def __delitem__(self, key):
        if not self._readonly:
            del self._payload[key]

    def __iter__(self):
        return iter(self._payload)

    def __len__(self):
        return len(self._payload)

    @contextmanager
    def readonly(self):
        try:
            self._readonly = True
            yield self
        finally:
            self._readonly = False
