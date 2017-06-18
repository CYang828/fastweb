# coding:utf8


import unittest

import init
from fastweb.util.configuration import Configuration


class ConfigurationTest(unittest.TestCase):

    def runTest(self):
        configuration = Configuration('ini', path='config/config.ini')
        print configuration.configs
        print configuration.get_components('mysql')

if __name__ == '__main__':
    unittest.main()
