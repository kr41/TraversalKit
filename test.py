import re

from nose import tools

from traversalkit import Resource, ANY_ID, DEC_ID, HEX_ID, TEXT_ID


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


sr = SiteRoot()


def test_repr():
    tools.eq_(repr(sr), '<SiteRoot: />')
    tools.eq_(repr(sr['user']), '<Users: /user/>')
    tools.eq_(repr(sr['user']['john']), '<User: /user/john/>')


def test_set_ids():
    tools.eq_(repr(sr['user']['john']), '<User: /user/john/>')
    tools.eq_(repr(sr['user']['jane']), '<User: /user/jane/>')
    tools.eq_(
        repr(sr['blog']['1-first-post']),
        '<BlogPost: /blog/1-first-post/>'
    )
    tools.eq_(
        repr(sr['blog']['2-post_no_2']),
        '<BlogPost: /blog/2-post_no_2/>'
    )


def test_any_id():
    tools.eq_(
        repr(sr['blog']['1-first-post']['Some File 123']),
        '<File: /blog/1-first-post/Some File 123/>'
    )


def test_built_in_regexp():
    tools.ok_(TEXT_ID.match('Jane_Doe-1984'))
    tools.ok_(not TEXT_ID.match('Jane Doe.1984'))
    tools.ok_(DEC_ID.match('42'))
    tools.ok_(not DEC_ID.match('2A'))
    tools.ok_(HEX_ID.match('2Af'))
    tools.ok_(not HEX_ID.match('2h'))


def test_lineage():
    lineage = list(sr['user']['john'].lineage())
    tools.eq_(lineage[0], sr['user']['john'])
    tools.eq_(lineage[1], sr['user'])
    tools.eq_(lineage[2], sr)


def test_cache():
    users = sr['user']
    tools.ok_(users is sr['user'])
    sr.__cache__.clear()
    tools.ok_(users is not sr['user'])


def test_parent():
    blog = sr['blog']
    post = blog['1-first-post']

    tools.eq_(post.parent(''), sr)
    tools.eq_(post.parent('user'), None)
    tools.eq_(post.parent('blog'), blog)
    tools.eq_(post.parent(cls='SiteRoot'), sr)
    tools.eq_(post.parent(cls='User'), None)
    tools.eq_(post.parent(cls='Blog'), blog)
    tools.eq_(post.parent(), blog)


def test_mount_as_method():
    SiteRoot.mount('privacy-policy', File)
    tools.eq_(repr(sr['privacy-policy']), '<File: /privacy-policy/>')


def test_mount_set_as_method():
    User.mount_set(TEXT_ID, File)
    tools.eq_(
        repr(sr['user']['john']['some_file']),
        '<File: /user/john/some_file/>'
    )


def test_implicit_child_call():
    ua = sr.child(File, 'user-agreement', 'Some Content')
    tools.eq_(repr(ua), '<File: /user-agreement/>')
    tools.eq_(ua.content, 'Some Content')


def test_implicit_child_cache():
    ua1 = sr.child(File, 'user-agreement', 'Some Content')
    tools.ok_(ua1 is sr['user-agreement'])
    ua2 = sr.child(File, 'user-agreement', 'Some Other Content')
    tools.ok_(ua2 is sr['user-agreement'])
    tools.ok_(ua1 is not ua2)              # Cache should be updated


@tools.raises(KeyError)
def test_key_error_on_direct_matching():
    sr['group']


@tools.raises(KeyError)
def test_key_error_on_pattern_matching():
    sr['blog']['1']


@tools.raises(KeyError)
def test_key_error_on_not_exist():
    sr['user']['john']['nonexistent-file']


@tools.raises(IOError)
def test_ignoring_not_exist():
    File('nonexistent-file')
