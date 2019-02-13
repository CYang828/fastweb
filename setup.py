# coding=utf-8


import sys
from setuptools import setup, find_packages


kwargs = {}
install_requires = []
version = '1.6.0.16'

if sys.version_info < (3, 0):
    with open('README.md') as f:
        kwargs['long_description'] = f.read()

    with open('requirements.txt') as f:
        for require in f:
            install_requires.append(require[:-1])
    install_requires.append('subprocess32')
elif sys.version_info > (3, 0):
    with open('README.md', encoding='utf-8') as f:
        kwargs['long_description'] = f.read()

    with open('requirements.txt', encoding='utf-8') as f:
        for require in f:
            install_requires.append(require[:-1])

if sys.platform.startswith('linux'):
    install_requires.append('readline')
elif sys.platform.startswith('win'):
    install_requires.append('pyreadline')

kwargs['install_requires'] = install_requires

setup(
    name='fastweb',
    version=version,
    include_package_data=True,
    packages=find_packages(),
    package_data={'fastweb': ['setting/default_logging.yaml']},
    entry_points={
        'console_scripts': [
            'fasthrift = fastweb.command.service.thrift:gen_thrift_auxiliary',
            'fast = fastweb.command.fast:main'
        ],
    },
    author='bslience',
    description="FastWeb is a web-server integration solution.",
    **kwargs
)
