from collections import MutableMapping
from contextlib import contextmanager


class Cache(MutableMapping):

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
