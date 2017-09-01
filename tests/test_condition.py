from traversalkit.condition import Under, Recursion


class A(object):
    pass


class B(object):
    pass


class C(object):
    pass


class NodeMock(object):

    def __init__(self, class_, name):
        self.class_ = class_
        self.name = name


def test_under():
    route = [NodeMock(A, 'a'), NodeMock(B, 'b')]
    assert Under(C)(route) is False
    assert Under(B)(route) is True
    assert Under('b')(route) is True
    assert Under(C, 'a')(route) is True
    assert Under(A, 'c')(route) is True


def test_recursion():
    route = [
        NodeMock(A, 'a'), NodeMock(B, 'b'),
        NodeMock(A, 'a'), NodeMock(B, 'b'),
    ]
    assert Recursion(maxdepth=1)(route) is False
    assert Recursion(maxdepth=2)(route) is True


def test_composition():
    condition = ~Under(A) & Recursion(maxdepth=1)
    assert condition([NodeMock(A, 'a'), NodeMock(B, 'b')]) is False
    assert condition([NodeMock(B, 'a'), NodeMock(B, 'b')]) is False
    assert condition([NodeMock(B, 'b')]) is True

    condition = Under(A) | Under('a')
    assert condition([NodeMock(A, 'a'), NodeMock(B, 'b')]) is True
    assert condition([NodeMock(B, 'a'), NodeMock(B, 'b')]) is True
    assert condition([NodeMock(B, 'b'), NodeMock(B, 'b')]) is False


def test_repr():
    repr(Under(A, 'a')) == "Under(<class A>, 'a')"
    repr(~Under(A, 'a')) == "Not(Under(<class A>, 'a'))"
    repr(Under(A, 'a') & Recursion(maxdepth=1)) == \
        "And(Under(<class A>, 'a'), Recursion(maxdepth=1)))"
    repr(Under(A) | Recursion(maxdepth=1)) == \
        "Or(Under(<class A>, 'a'), Recursion(maxdepth=1)))"
