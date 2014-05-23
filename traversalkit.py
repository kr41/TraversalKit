import re


__all__ = ['Resource']
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

    @classmethod
    def mount(cls, name, class_=None):
        def decorator(class_):
            cls._children_map[name] = class_
            return class_
        if class_ is not None:
            return decorator(class_)
        return decorator

    @classmethod
    def mount_set(cls, pattern, class_=None):
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
        pass

    def child(self, cls, name, payload=None):
        child = self.__cache__[name] = cls(name, self, payload)
        return child

    def __getitem__(self, name):
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
        resource = self
        while resource:
            yield resource
            resource = resource.__parent__

    def parent(self, name=None, cls=None):
        if name is not None:
            check = lambda r: r.__name__ == name
        elif cls is not None:
            check = lambda r: r.__class__.__name__ == cls
        else:
            return self.__parent__
        for resource in self.lineage():
            if check(resource):
                return resource
        return None
