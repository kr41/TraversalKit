import weakref
from itertools import chain
from contextlib import contextmanager
from warnings import warn

from cached_property import cached_property

from .route import Node, Route
from .cache import Cache


class ResourceMeta(type):
    """ Resource Meta Class """

    def __init__(cls, class_name, bases, attrs):
        cls._children_map = {}
        cls._children_set = []
        cls._named_nodes = {}
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

    __nodeclass__ = Node
    __routeclass__ = Route
    __cacheclass__ = Cache

    ##
    # Resource tree manipulation and introspection
    #

    @classmethod
    def mount(cls, name, class_=None, **kw):
        """
        Mounts single named child resource to current one.

        The method can be used as a decorator.

        """
        def decorator(class_):
            node = cls.__nodeclass__(class_, name=name, **kw)
            cls._children_map[name] = node
            cls._named_nodes[name] = node
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    @classmethod
    def mount_set(cls, pattern, class_=None, **kw):
        """
        Mounts set of child resources to current one.

        A ``pattern`` argument should be compiled regular expression object
        or any object, which provides ``match`` method.  If you are going
        match any child's name use ``ANY_ID`` constant.

        The method can be used as a decorator.

        """
        def decorator(class_):
            node = cls.__nodeclass__(class_, pattern=pattern, **kw)
            cls._children_set.append(node)
            if node.metaname is not None:
                cls._named_nodes[node.metaname] = node
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    @classmethod
    def routes(cls, route=None):
        if route is None:
            route = cls.__routeclass__(cls.__nodeclass__(cls, name=''))
        yield route

        single_nodes = (cls._children_map[name]
                        for name in sorted(cls._children_map.keys()))
        set_nodes = (node for node in cls._children_set)

        for node in chain(single_nodes, set_nodes):
            this_route = route + node
            if node.complies is None or node.complies(this_route):
                for sub_route in node.class_.routes(this_route):
                    yield sub_route

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

        It's called from :meth:`__init__` method.  When resource is created
        within parent's :meth:`__getitem__` method, ``payload`` argument
        will be ``None``.

        Derived classes must override this method instead of
        :meth:`__init__` one.

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
        try:
            node = self._named_nodes[name]
        except KeyError:
            raise KeyError(name, self.uri)
        if not node.complies(self.__route__):
            raise KeyError(name, self.uri)

        def add_child(name, payload=None):
            return self._child(node, name, payload=payload)

        yield add_child

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

    ##
    # Deprecated methods
    #

    def child(self, class_, name, payload=None):
        """
        ..  warning:: Deprecated in favor of :meth:`node`.

        Creates child resource from given class and name.

        Optional argument ``payload`` will be passed to :meth:`on_init`
        method.

        The method overrides any cache entry for given name.
        It also doesn't validate child's name and doesn't catch any exception
        child raises.

        """
        warn('Method ``child`` is deprected '
             'in favor of ``node`` context manager',
             DeprecationWarning)
        node = self.__nodeclass__(class_, name=name)
        return self._child(node, name, payload=payload)
