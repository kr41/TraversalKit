from traversalkit.cache import Cache


def test_cache():
    cache = Cache()

    cache['x'] = 1
    assert cache == {'x': 1}
    assert cache['x'] == 1
    assert cache.get('x') == 1
    assert cache.get('y') is None
    assert cache.setdefault('y', 2) == 2
    assert cache == {'x': 1, 'y': 2}

    del cache['y']
    assert cache == {'x': 1}
    assert len(cache) == 1
    assert [key for key in cache] == ['x']

    cache['y'] = 2
    with cache.readonly():
        del cache['y']
        assert cache == {'x': 1, 'y': 2}

        cache['z'] = 3
        assert cache == {'x': 1, 'y': 2}

    cache['z'] = 3
    assert cache == {'x': 1, 'y': 2, 'z': 3}
