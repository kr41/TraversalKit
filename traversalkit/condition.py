try:  # pragma: no cover
    string = basestring
except NameError:  # pragma: no cover
    string = str


class Condition(object):

    def __call__(self, route):  # pragma: no cover
        raise NotImplementedError('The method should be overriden')

    def __invert__(self):
        return Not(self)

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __repr__(self):
        params = (
            '%s=%r' % (key, value)
            for key, value in self.__dict__.items()
        )
        params = ', '.join(params)
        return '%s(%s)' % (self.__class__.__name__, params)


class Not(Condition):

    def __init__(self, condition):
        self.condition = condition

    def __call__(self, route):
        return not self.condition(route)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.condition)


class And(Condition):

    def __init__(self, left, rigth):
        self.left = left
        self.rigth = rigth

    def __call__(self, route):
        return self.left(route) and self.rigth(route)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.left, self.rigth)


class Or(Condition):

    def __init__(self, left, rigth):
        self.left = left
        self.rigth = rigth

    def __call__(self, route):
        return self.left(route) or self.rigth(route)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.left, self.rigth)


class Under(Condition):

    def __init__(self, *parents):
        self.parents = parents

    def __call__(self, route):
        for node in route:
            if node.class_ in self.parents:
                return True
            if node.name is not None and node.name in self.parents:
                return True
        return False

    def __repr__(self):
        parents = (repr(p) for p in self.parents)
        parents = ', '.join(parents)
        return '%s(%s)' % (self.__class__.__name__, parents)


class Recursion(Condition):

    def __init__(self, maxdepth):
        self.maxdepth = maxdepth

    def __call__(self, route):
        depth = 0
        target = route[-1]
        for node in route:
            if node.class_ is target.class_:
                depth += 1
        return self.maxdepth >= depth
