"""
Traversal Kit
-------------

The library provides base class :class:`Resource` to build hierarchy
of `location-aware resources`_, which will be used in Pyramid_ application
using traversal_.


::  _Pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
::  _traversal: http://docs.pylonsproject.org/projects/pyramid/en/latest/
                narr/traversal.html
::  _location aware resources: http://docs.pylonsproject.org/projects/pyramid/
                               en/latest/narr/resources.html#
                               location-aware-resources

"""

import re


__all__ = ['Resource', 'ANY_ID', 'DEC_ID', 'HEX_ID', 'TEXT_ID']
__version__ = '0.1'
__author__ = 'Dmitry Vakhrushev <self@kr41.net>'
__license__ = 'BSD'


ANY_ID = object()
DEC_ID = re.compile(r'^[\d]+$')
HEX_ID = re.compile(r'^[a-f\d]+$', re.I)
TEXT_ID = re.compile(r'^[\w\-]+$', re.I)


class ResourceMeta(type):
    """ Resource Meta Class """

    def __init__(cls, class_name, bases, attrs):
        cls._children_map = {}
        cls._children_set = []
        cls.__not_exist__ = getattr(cls, '__not_exist__', None)


# For compatibility between Python 2.x and Python 3.x
BaseResource = ResourceMeta('BaseResource', (object,), {})


class Resource(BaseResource):
    """ Base class for resources, which are used in traversal hierarchy """

    @classmethod
    def mount(cls, name, class_=None):
        """
        Mounts single named child resource to current one.

        The method can be used as a decorator.

        """
        def decorator(class_):
            cls._children_map[name] = class_
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    @classmethod
    def mount_set(cls, pattern, class_=None):
        """
        Mounts set of child resources to current one.

        A ``pattern`` argument should be compiled regular expression object
        or any object which provides ``match`` method.  If you are going
        match any child's name use ``ANY_ID`` constant.

        The method can be used as a decorator.

        """
        def decorator(class_):
            cls._children_set.append((pattern, class_))
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    def __init__(self, name='', parent=None, payload=None):
        self.__name__ = name
        self.__parent__ = parent
        self.__cache__ = {}
        self.on_init(payload)

    def on_init(self, payload):
        """
        Initialization callback.

        It's called from ``__init__`` method.  When resource is created
        within parent's ``__getitem__`` method, ``payload`` argument
        will be ``None``.

        Derived classes must override this method instead of ``__init__`` one.

        """

    def child(self, cls, name, payload=None):
        """
        Creates child resource from given class and name.

        Optional argument ``payload`` will be passed to :meth:`on_load`
        method.

        The method overrides any cache entry for given name.
        It also doesn't validate child's name and doesn't catch any exception
        child raises.

        """
        child = self.__cache__[name] = cls(name, self, payload)
        return child

    def __getitem__(self, name):
        """
        Returns child resource by its name.

        Child resource class should be mounted using :meth:`mount` or
        :meth:`mount_set` methods.

        The method uses cache.  Therefore it won't create child resource,
        if it's already created using this method or method :meth:`child`.
        It also catches exceptions of child's ``__not_exist__`` attribute
        and turns them to ``KeyError``.

        """
        try:
            return self.__cache__[name]
        except KeyError:
            try:
                factory = self._children_map[name]
            except KeyError:
                for pattern, class_ in self._children_set:
                    if pattern is ANY_ID or pattern.match(name):
                        factory = class_
                        break
                else:
                    raise
            try:
                return self.child(factory, name)
            except Exception as e:
                if factory.__not_exist__ and \
                   isinstance(e, factory.__not_exist__):
                    raise KeyError(name)
                raise

    def __repr__(self):
        url = [r.__name__ for r in self.lineage()]
        url.reverse()
        url.append('')
        return '<{0}: {1}>'.format(self.__class__.__name__, '/'.join(url))

    def lineage(self):
        """
        Returns iterator over resource parents.

        Lineage chain includes current resource.

        """
        resource = self
        while resource:
            yield resource
            resource = resource.__parent__

    def parent(self, name=None, cls=None):
        """
        Searches particular parent in the resource lineage.

        Search can be done by parent's name, as well as by parent's class
        (using ``cls`` argument).

        The ``cls`` argument accepts class name, as well as class itself.

        """
        if name is not None:
            check = lambda r: r.__name__ == name
        elif cls is not None:
            if isinstance(cls, type):
                check = lambda r: r.__class__ is cls
            else:
                check = lambda r: r.__class__.__name__ == cls
        else:
            return self.__parent__
        for resource in self.lineage():
            if check(resource):
                return resource
        return None
