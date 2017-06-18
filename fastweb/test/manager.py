# coding:utf8


import unittest

import init

from fastweb import app
from fastweb import ioloop
from fastweb.manager import Manager
from fastweb.pattern import SyncPattern, AsynPattern


class ManagerTest(unittest.TestCase):

    def runTest(self):
        app.load_configuration('config/config.ini')
        self.manager = Manager(pattern=SyncPattern)
        self.manager.setup()
        #ioloop.IOLoop.instance().run_sync(self.manager.setup() )

if __name__ == '__main__':
    unittest.main()
