import re

import pytest

from traversalkit import Resource, ANY_ID, TEXT_ID, condition


@pytest.fixture
def resources():
    class SiteRoot(Resource):
        """ Web site root resource """

    @SiteRoot.mount('user')
    class Users(Resource):
        """ Collection of users """

    @Users.mount_set(TEXT_ID, metaname='username')
    class User(Resource):
        """ User resource """

    @User.mount('blog')
    @SiteRoot.mount('blog')
    class Blog(Resource):
        """
        Blog resource

        Each user has a blog. There is also a blog of site administrators,
        which is available at the site root.

        """

    @Blog.mount_set(re.compile(r'^[\d]+-[\w\-]+$', re.I), metaname='post_id')
    class BlogPost(Resource):
        """ Blog post resource """

    @BlogPost.mount('comments', complies=condition.Under(User))
    class Comments(Resource):
        """
        Blog post comments

        This resource is only available for user blogs,
        but not for the blog of site administrators (at the site root).

        """

    @BlogPost.mount_set(ANY_ID, metaname='filename')
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

    return {
        class_.__name__: class_
        for class_ in locals().values()
        if isinstance(class_, type) and issubclass(class_, Resource)
    }


@pytest.fixture
def root(resources):
    return resources['SiteRoot']()


def test_repr(root):
    assert repr(root) == '<SiteRoot: />'
    assert repr(root['user']) == '<Users: /user/>'
    assert repr(root['user']['john']) == '<User: /user/john/>'


def test_routes(resources):
    result = [route.uri for route in resources['SiteRoot'].routes()]
    assert result == [
        '/',
        '/blog/',
        '/blog/{post_id}/',
        '/blog/{post_id}/{filename}/',
        '/error/',
        '/user/',
        '/user/{username}/',
        '/user/{username}/blog/',
        '/user/{username}/blog/{post_id}/',
        '/user/{username}/blog/{post_id}/comments/',
        '/user/{username}/blog/{post_id}/{filename}/',
    ]


def test_set_ids(root):
    assert repr(root['user']['john']) == '<User: /user/john/>'
    assert repr(root['user']['jane']) == '<User: /user/jane/>'
    assert repr(root['blog']['1-first-post']) == \
        '<BlogPost: /blog/1-first-post/>'
    assert repr(root['blog']['2-post_no_2']) == \
        '<BlogPost: /blog/2-post_no_2/>'


def test_any_id(root):
    assert repr(root['blog']['1-first-post']['Some File 123']) == \
        '<File: /blog/1-first-post/Some File 123/>'


def test_lineage(root):
    lineage = list(root['user']['john'].lineage())
    assert lineage[0] == root['user']['john']
    assert lineage[1] == root['user']
    assert lineage[2] == root


def test_resource_route_and_node(root):
    assert root.__route__.uri == '/'
    assert root.__node__ == root.__route__[-1]

    user = root['user']
    assert user.__route__.uri == '/user/'
    assert user.__node__ == user.__route__[-1]

    john = user['john']
    assert john.__route__.uri == '/user/{username}/'
    assert john.__node__ == john.__route__[-1]


def test_cache(root):
    users = root['user']
    assert users is root['user']
    root.__cache__.clear()
    assert users is not root['user']


def test_parent(root, resources):
    blog = root['blog']
    post = blog['1-first-post']

    assert post.parent('') == root
    assert post.parent('user') is None
    assert post.parent('blog') == blog
    assert post.parent(cls='SiteRoot') == root
    assert post.parent(cls=resources['SiteRoot']) == root
    assert post.parent(cls='User') is None
    assert post.parent(cls=resources['User']) is None
    assert post.parent(cls='Blog') == blog
    assert post.parent(cls=resources['Blog']) == blog
    assert post.parent() == blog


def test_mount_as_method(root, resources):
    resources['SiteRoot'].mount('privacy-policy', resources['File'])
    assert repr(root['privacy-policy']) == '<File: /privacy-policy/>'


def test_mount_set_as_method(root, resources):
    resources['User'].mount_set(TEXT_ID, resources['File'])
    assert repr(root['user']['john']['some_file']) == \
        '<File: /user/john/some_file/>'


def test_explicit_child_call(root, resources):
    ua = root.child(resources['File'], 'user-agreement', 'Some Content')
    assert repr(ua) == '<File: /user-agreement/>'
    assert ua.content == 'Some Content'


def test_implicit_child_cache(root, resources):
    ua1 = root.child(resources['File'], 'user-agreement', 'Some Content')
    assert ua1 is root['user-agreement']

    ua2 = root.child(resources['File'], 'user-agreement', 'Some Other Content')
    assert ua2 is root['user-agreement']
    assert ua1 is not ua2   # Cache should be updated


def test_key_error_on_direct_matching(root):
    with pytest.raises(KeyError) as info:
        root['group']

    assert info.value.args == ('group', '/')


def test_key_error_on_pattern_matching(root):
    with pytest.raises(KeyError) as info:
        root['blog']['1']

    assert info.value.args == ('1', '/blog/')


def test_key_error_on_restriction(root):
    root['user']['john']['blog']['1-some_post']['comments']

    with pytest.raises(Exception) as info:
        root['blog']['1-some_post']['comments']

    assert info.value.args == ('comments', '/blog/1-some_post/')


def test_key_error_on_not_exist(root):
    with pytest.raises(KeyError) as info:
        root['blog']['1-some_post']['nonexistent-file']

    assert info.value.args == ('nonexistent-file', '/blog/1-some_post/')


def test_ignoring_not_exist(resources):
    with pytest.raises(IOError):
        resources['File']('nonexistent-file')


def test_error_propagation(root):
    with pytest.raises(Exception):
        root['error']
