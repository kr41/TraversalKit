import os
from setuptools import setup

version = '0.1'
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    readme = f.read()

setup(
    name='TraversalKit',
    version=version,
    description='Helper library for Pyramid applications based on Traversal',
    long_description=readme,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Framework :: Pyramid',
    ],
    keywords='pyramid traversal resources',
    author='Dmitry Vakhrushev',
    author_email='self@kr41.net',
    url='https://bitbucket.org/kr41/traversalkit',
    download_url='https://bitbucket.org/kr41/traversalkit/downloads',
    license='BSD',
    test_suite='nose.collector',
    py_modules=['traversalkit'],
    zip_safe=True,
)
