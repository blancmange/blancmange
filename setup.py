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
    'requests',
    'ipython',
    'ipdb',
    ]

setup(name='its',
      version='0.1dev0',
      description='its',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='David Beitey',
      author_email='qnivq@qnivqwo.pbz'.decode('rot-13'),
      url='http://davidjb.com',
      keywords='python keywords flying circus',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      setup_requires=[],#['setuptools-git'],
      entry_points="""\
      [console_scripts]
      its = its:main
      """,
      )
