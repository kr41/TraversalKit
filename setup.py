import os
from setuptools import setup, find_packages

version = '0.3.1'
here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    long_description = '\n' + f.read()

with open(os.path.join(here, 'CHANGES.rst')) as f:
    long_description += '\n\n' + f.read()


requirements = ['cached_property']

setup(
    name='TraversalKit',
    version=version,
    description='Helper library for Pyramid applications based on Traversal',
    long_description=long_description,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
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
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=requirements,
    zip_safe=True,
)
