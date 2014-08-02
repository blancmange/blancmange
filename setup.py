import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'sqlalchemy',
    'zope.sqlalchemy',
    'transaction',
    'pytvdbapi',
    'jedi',
    'textblob',
    'pyquery',
    'lxml',
    'pygments',
    'ipython',
    'ipdb',
    ]

setup(name='blancmange',
      version='0.2',
      description="Determine what's missing from Python by using Monty Python's Flying Circus.",
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        ],
      author='David Beitey',
      author_email='david' + chr(64) + 'davidjb.com',
      url='http://github.com/davidjb/blancmange',
      keywords='python keywords flying circus blancmange',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      setup_requires=['setuptools-git'],
      entry_points="""\
      [console_scripts]
      blancmange = blancmange:main
      flying-circus-db = blancmange:create_database
      flying-circus = blancmange:flying_circus_stats
      spot-camels = blancmange:find_episode
      completely-different = blancmange:completely_different
      """,
      )
