import re

from traversalkit.route import Node, Route


def test_node():
    node = Node(object, name='foo')
    assert str(node) == 'foo'
    assert repr(node) == '<Node: foo>'
    assert node.type == 'single'

    node = Node(object, metaname='foo')
    assert str(node) == '{foo}'
    assert repr(node) == '<Node: {foo}>'
    assert node.type == 'set'

    node = Node(object, pattern=re.compile('.*'))
    assert str(node) == '{.*}'
    assert repr(node) == '<Node: {.*}>'
    assert node.type == 'set'

    node = Node(object)
    assert str(node) == '*'
    assert repr(node) == '<Node: *>'
    assert node.type == 'set'


def test_path():
    path = Route()
    assert path.uri == '*'
    assert repr(path) == '<Route: *>'
    assert len(path) == 0

    path += Node(object, name='')
    assert path.uri == '/'
    assert repr(path) == '<Route: />'
    assert len(path) == 1

    path += [Node(object, name='foo'), Node(object, metaname='bar')]
    assert path.uri == '/foo/{bar}/'
    assert repr(path) == '<Route: /foo/{bar}/>'
    assert len(path) == 3
