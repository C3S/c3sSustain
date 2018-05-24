import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    #'Babel',
    'Babel==1.3',
    'colander==1.0',
    'cryptacular==1.4.1',
    'deform==2.0a2',
    'lingua==3.6.1',
    'pyramid==1.5.2',
    'pyramid_beaker==0.8',
    'pyramid_chameleon==0.3',
    'pyramid_debugtoolbar==2.2.2',
    'pyramid_mailer==0.13',
    'pyramid_tm==0.8',
    'python-gnupg==0.3.6',
    'SQLAlchemy==0.9.8',
    'transaction==1.4.3',
    'zope.sqlalchemy==0.7.5',
    'waitress==0.8.9',
]
test_requires = [
    'coverage',
    'nose',
    #'nose-cov',
    'webtest',
]
setup(name='zabo',
      version='0.0',
      description='zabo',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='zabo',
      install_requires=requires+test_requires,
      entry_points="""\
      [paste.app_factory]
      main = zabo:main
      [console_scripts]
      initialize_zabo_db = zabo.scripts.initializedb:main
      """,
      message_extractors={
          'zabo': [
              ('**.py', 'lingua_python', None),
              ('**.pt', 'lingua_xml', None),
          ]
      }
      )
