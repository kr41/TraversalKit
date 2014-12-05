TraversalKit
============

TraversalKit helps you to build Pyramid_ applications, which use traversal_
as their routing method.  It provides single base class ``Resource``,
which your ones should inherit.  The base class has a handful of features
have been done for you, which includes `location-awareness`_,
mounting resources to each-other to build a resource tree, and resource lineage
inspection.

Quick example of usage:

..  code-block:: python

    from traversalkit import Resource, DEC_ID


    class SiteRoot(Resource):
        """ Root resource of your site """

    @SiteRoot.mount('blog')
    class Blog(Resource):
        """ Blog resource will be available under the URL: /blog/ """

    @Blog.mount_set(DEC_ID)
    class BlogPost(Resource):
        """
        Blog post resource will be available under the URL: /blog/xxx

        Where ``xxx`` is a decimal number

        """

Pretty neat and simple, isn't it?  Look over `the example application`_ and
`library source code`_ (it's really compact, I swear) to learn how TraversalKit
can be used.

Even though the library was developed to be used within Pyramid applications,
it doesn't have any dependencies.  So if you find out that it is useful
in your non-Pyramid application, feel free to get it.


..  _Pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
..  _traversal: http://docs.pylonsproject.org/projects/pyramid/en/latest/
                narr/traversal.html
..  _location-awareness: http://docs.pylonsproject.org/projects/pyramid/
                         en/latest/narr/resources.html#location-aware-resources
..  _the example application: https://bitbucket.org/kr41/traversalkitexampleapp
..  _library source code:  https://bitbucket.org/kr41/traversalkit/src
