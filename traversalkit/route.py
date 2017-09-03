"""
The module provides route descriptors.

The following classes should not be instantiated directly.
They are used within :class:`traversalkit.resource.Resource` to handle routes.

"""


from collections import Sequence
from itertools import chain

from cached_property import cached_property


class Node(object):
    """
    Route node descriptor.

    :param Resource class_: Resource class of the node.
    :param str name: Name of the node. Optional.
    :param regex pattern: Pattern of node name. Optional.
    :param str metaname: Metaname of node. Optional.
    :param Condition complies: Condition that route should complie. Optional.


    ..  attribute:: class_

        Resource class of the node. Should be a subclass of
        :class:`traversalkit.resource.Resource`


    ..  attribute:: name

        Name of the node.  It is specified, when the node is created by
        :meth:`traversalkit.resource.Resource.mount`.


    ..  attribute:: pattern

        Pattern of the node name.  It is specified, when the node is created by
        :meth:`traversalkit.resource.Resource.mount_set`.

    ..  attribute:: metaname

        Metaname of the node.  It is specified, when the node is created by
        :meth:`traversalkit.resource.Resource.mount_set`.


    ..  attribute:: type

        Type of the node.

        If :attr:`name` is defined, the ``type`` will be ``"single"``,
        i.e. the node has been created using
        :meth:`traversalkit.resource.Resource.mount`.

        If :attr:`name` is not defined, the ``type`` will be ``"set"``,
        i.e. the node has been created using
        :meth:`traversalkit.resource.Resource.mount_set`.

    """

    def __init__(self, class_, name=None, pattern=None, metaname=None,
                 complies=None):
        self.class_ = class_
        self.name = name
        self.pattern = pattern
        self.metaname = metaname
        self._complies = complies

    @cached_property
    def type(self):
        return 'single' if self.name is not None else 'set'

    def complies(self, route):
        """
        Checks whether the route complies node's condition.

        If the node has been created without ``complies`` parameter,
        this method will always return ``True``.

        If the node has been created with ``complies`` parameter,
        this method will run ``compiles(route + self)`` (i.e. passes
        the route concatenated with the node itself to the condition)
        and return the result. See :mod:`traversalkit.condition` for details.

        :param Route route: Route to test.
        :return: Result of the test.
        :rtype: bool

        """
        if self._complies is None:
            return True
        return self._complies(route + self)

    def __str__(self):
        """
        String representation of the node.

        It is mostly useful for documentation purposes.
        There are three possible representations:

        ..  doctest::

            >>> import re

            >>> # Node describes single named resource
            >>> node = Node(object, name='foo')
            >>> str(node)
            'foo'

            >>> # Node describes anonymous set of resources
            >>> node = Node(object, pattern=re.compile('.*'))
            >>> str(node)
            '{.*}'

            >>> # Node describes named set of resources
            >>> node = Node(object, pattern=re.compile('.*'),
            ...             metaname='foo')
            >>> str(node)
            '{foo}'

        """
        if self.name is not None:
            return self.name
        elif self.metaname is not None:
            return '{%s}' % self.metaname
        elif self.pattern is not None:
            return '{%s}' % self.pattern.pattern
        return '*'

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self)


class Route(Sequence):
    """
    Route descriptor.

    In general, it is just a immutable sequence of nodes (see :class:`Node`)
    with some syntactic surgar.

    :param Node *nodes: Nodes of the route.

    ..  doctest::

        >>> import re
        >>> route = Route(Node(object, name=''))
        >>> route
        <Route: />
        >>> len(route)
        1
        >>> route.uri
        '/'

        >>> route += Node(object, name='foo')
        >>> route
        <Route: /foo/>
        >>> len(route)
        2
        >>> route.uri
        '/foo/'

        >>> route += [
        ...     Node(object, pattern=re.compile(r'.*')),
        ...     Node(object, pattern=re.compile(r'.*'), metaname='bar'),
        ... ]
        >>> route
        <Route: /foo/{.*}/{bar}/>
        >>> len(route)
        4
        >>> route.uri
        '/foo/{.*}/{bar}/'

    """

    def __init__(self, *nodes):
        self.nodes = nodes

    def __getitem__(self, index):
        return self.nodes[index]

    def __len__(self):
        return len(self.nodes)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.uri)

    def __add__(self, other):
        if not isinstance(other, Sequence):
            other = [other]
        return self.__class__(*chain(self, other))

    @cached_property
    def uri(self):
        return '/'.join(str(n) for n in self) + '/' if self else '*'
