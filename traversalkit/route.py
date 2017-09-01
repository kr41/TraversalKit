from collections import Sequence
from itertools import chain

from cached_property import cached_property


class Node(object):

    def __init__(self, class_, name=None, pattern=None, metaname=None,
                 complies=None):
        self.class_ = class_
        self.name = name
        self.pattern = pattern
        self.metaname = metaname
        self.complies = complies

    @cached_property
    def type(self):
        return 'single' if self.name is not None else 'set'

    def __str__(self):
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
