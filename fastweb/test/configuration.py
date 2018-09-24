# coding:utf8


import unittest

import init
from fastweb.util.configuration import ConfigurationParser


class ConfigurationTest(unittest.TestCase):

    def runTest(self):
        configuration = ConfigurationParser('ini', path='config/config.ini')
        print((configuration.configs))
        print((configuration.get_components('mysql')))


if __name__ == '__main__':
    unittest.main()
