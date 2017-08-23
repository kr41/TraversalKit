"""
The library provides base class :class:`Resource` to build hierarchy
of `location-aware resources`_, which will be used in Pyramid_ application
using traversal_.


..  _Pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
..  _traversal: http://docs.pylonsproject.org/projects/pyramid/en/latest/
                narr/traversal.html
..  _location-aware resources: http://docs.pylonsproject.org/projects/pyramid/
                               en/latest/narr/resources.html#
                               location-aware-resources

It also provides most common name pattens, which can be used with
:meth:`Resource.mount_set` method:

    ``ANY_ID``
        Switch off matching
    ``DEC_ID``
        Matches decimal names only: ``^[\d]+$``
    ``HEX_ID``
        Matches hexadecimal names only: ``^[a-f\d]+$``
    ``TEXT_ID``
        Matches single word: ``^[\w\-]+$``

"""

import weakref
import re


__all__ = ['Resource', 'ANY_ID', 'DEC_ID', 'HEX_ID', 'TEXT_ID']
__version__ = '0.2'
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
    """
    Base class for resources, which are used in traversal hierarchy

    Derived classes may define class attribute ``__not_exist__``, which
    should be an exception class or tuple of ones.  These exceptions will
    be caught within :meth:`__getitem__` method of parent object and will
    be turned into ``KeyError`` one.

    Each resource object has following attributes:

        ``__name__``
            Resource name, as it was passed to parent's :meth:`__getitem__`
            or :meth:`child` method.
        ``__parent__``
            Link to a parent resource.  It's actually property, which
            stores weak reference to a parent.
        ``__cache__``
            Cache of child resources, regular dictionary object.
            It's used by :meth:`__getitem__` method, whereas :meth:`child` one
            overrides it.

    """

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
        or any object, which provides ``match`` method.  If you are going
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

    @property
    def __parent__(self):
        return self.__parent()

    @__parent__.setter
    def __parent__(self, parent):
        self.__parent = weakref.ref(parent) if parent else lambda: None

    def on_init(self, payload):
        """
        Initialization callback.

        It's called from :meth:`__init__` method.  When resource is created
        within parent's :meth:`__getitem__` method, ``payload`` argument
        will be ``None``.

        Derived classes must override this method instead of
        :meth:`__init__` one.

        """

    def child(self, cls, name, payload=None):
        """
        Creates child resource from given class and name.

        Optional argument ``payload`` will be passed to :meth:`on_init`
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
        return self.get(name)

    def get(self, name, payload=None):
        """
        Returns child resource by its name.

        Optional argument ``payload`` will be passed to :meth:`on_init`
        method.

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
                return self.child(factory, name, payload)
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
