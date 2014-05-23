import os
from setuptools import setup

version = '0.1'
here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

setup(
    name='TraversalKit',
    version=version,
    description='',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Framework :: Pyramid',
    ],
    keywords='',
    author='Dmitry Vakhrushev',
    author_email='self@kr41.net',
    url='https://bitbucket.org/kr41/traversalkit',
    download_url='https://bitbucket.org/kr41/traversalkit/downloads',
    license='BSD',
    py_modules=['traversalkit'],
    zip_safe=True,
)
