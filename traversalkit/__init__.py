"""
The library provides base class :class:`Resource` to build hierarchy
of `location-aware resources`_, which will be used in Pyramid_ application
using traversal_.


..  _Pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
..  _traversal: http://docs.pylonsproject.org/projects/pyramid/en/latest/
                narr/traversal.html
..  _location-aware resources: http://docs.pylonsproject.org/projects/pyramid/
                               en/latest/narr/resources.html#
                               location-aware-resources

It also provides most common name pattens, which can be used with
:meth:`Resource.mount_set` method:

    ``ANY_ID``
        Switch off matching
    ``DEC_ID``
        Matches decimal names only: ``^[\d]+$``
    ``HEX_ID``
        Matches hexadecimal names only: ``^[a-f\d]+$``
    ``TEXT_ID``
        Matches single word: ``^[\w\-]+$``

"""


from .resource import Resource, ANY_ID, DEC_ID, HEX_ID, TEXT_ID


__all__ = ['Resource', 'ANY_ID', 'DEC_ID', 'HEX_ID', 'TEXT_ID']
__version__ = '0.2'
__author__ = 'Dmitry Vakhrushev <self@kr41.net>'
__license__ = 'BSD'
