# coding:utf8


from setuptools import setup, find_packages

kwargs = {}

version = '1.4.1.2'

with open('README.rst') as f:
        kwargs['long_description'] = f.read()

install_requires = []
with open('requirements.txt') as f:
    for require in f:
        install_requires.append(require[:-1])

kwargs['install_requires'] = install_requires

setup(
    name='fastweb',
    version=version,
    packages=find_packages(),
    package_data={'fastweb': ['setting/default_logging.yaml']},
    scripts=['requirements.txt'],
    entry_points={
        'console_scripts': [
            'fastthrift = fastweb.command.service.thrift:gen_thrift_auxiliary',
        ],
    },
    author='Bslience',
    description="FastWeb is a Python fast-building web frame refered by Tornado, Celery, Thrift",
    **kwargs
)
