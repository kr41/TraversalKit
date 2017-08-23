import re

import pytest

from traversalkit import Resource, ANY_ID, TEXT_ID


class SiteRoot(Resource):
    """ Web site root resource """


@SiteRoot.mount('user')
class Users(Resource):
    """ Collection of users """


@Users.mount_set(TEXT_ID)
class User(Resource):
    """ User resource """


@User.mount('blog')
@SiteRoot.mount('blog')
class Blog(Resource):
    """
    Blog resource

    Each user has a blog. There is also a blog of site administrators,
    which is available on site root.

    """


@Blog.mount_set(re.compile(r'^[\d]+-[\w\-]+$', re.I))
class BlogPost(Resource):
    """ Blog post resource """


@BlogPost.mount_set(ANY_ID)
class File(Resource):
    """ Static file resource """

    __not_exist__ = IOError

    def on_init(self, payload):
        if self.__name__ == 'nonexistent-file':
            with open('nonexistent-file') as f:
                self.content = f.read()     # This will never happen
        self.content = payload


@SiteRoot.mount('error')
class Error(Resource):
    """ It always raises error """

    def on_init(self, payload):
        raise Exception('Test')


sr = SiteRoot()


def test_repr():
    assert repr(sr) == '<SiteRoot: />'
    assert repr(sr['user']) == '<Users: /user/>'
    assert repr(sr['user']['john']) == '<User: /user/john/>'


def test_set_ids():
    assert repr(sr['user']['john']) == '<User: /user/john/>'
    assert repr(sr['user']['jane']) == '<User: /user/jane/>'
    assert repr(sr['blog']['1-first-post']) == \
        '<BlogPost: /blog/1-first-post/>'
    assert repr(sr['blog']['2-post_no_2']) == \
        '<BlogPost: /blog/2-post_no_2/>'


def test_any_id():
    assert repr(sr['blog']['1-first-post']['Some File 123']) == \
        '<File: /blog/1-first-post/Some File 123/>'


def test_lineage():
    lineage = list(sr['user']['john'].lineage())
    assert lineage[0] == sr['user']['john']
    assert lineage[1] == sr['user']
    assert lineage[2] == sr


def test_cache():
    users = sr['user']
    assert users is sr['user']
    sr.__cache__.clear()
    assert users is not sr['user']


def test_parent():
    blog = sr['blog']
    post = blog['1-first-post']

    assert post.parent('') == sr
    assert post.parent('user') is None
    assert post.parent('blog') == blog
    assert post.parent(cls='SiteRoot') == sr
    assert post.parent(cls=SiteRoot) == sr
    assert post.parent(cls='User') is None
    assert post.parent(cls=User) is None
    assert post.parent(cls='Blog') == blog
    assert post.parent(cls=Blog) == blog
    assert post.parent() == blog


def test_mount_as_method():
    SiteRoot.mount('privacy-policy', File)
    assert repr(sr['privacy-policy']) == '<File: /privacy-policy/>'


def test_mount_set_as_method():
    User.mount_set(TEXT_ID, File)
    assert repr(sr['user']['john']['some_file']) == \
        '<File: /user/john/some_file/>'


def test_implicit_child_call():
    ua = sr.child(File, 'user-agreement', 'Some Content')
    assert repr(ua) == '<File: /user-agreement/>'
    assert ua.content == 'Some Content'


def test_implicit_child_cache():
    ua1 = sr.child(File, 'user-agreement', 'Some Content')
    assert ua1 is sr['user-agreement']

    ua2 = sr.child(File, 'user-agreement', 'Some Other Content')
    assert ua2 is sr['user-agreement']
    assert ua1 is not ua2   # Cache should be updated


def test_key_error_on_direct_matching():
    with pytest.raises(KeyError):
        sr['group']


def test_key_error_on_pattern_matching():
    with pytest.raises(KeyError):
        sr['blog']['1']


def test_key_error_on_not_exist():
    with pytest.raises(KeyError):
        sr['user']['john']['nonexistent-file']


def test_ignoring_not_exist():
    with pytest.raises(IOError):
        File('nonexistent-file')


def test_error_propagation():
    with pytest.raises(Exception):
        sr['error']
