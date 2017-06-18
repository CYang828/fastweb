# coding:utf8


import time
import unittest

from fastweb import ioloop
from fastweb.component.db.mysql import SyncMysql, AsynMysql
from fastweb.loader import app
from fastweb.pool import ConnectionPool, SyncConnectionPool, AsynConnectionPool

app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')


class ConnectionPoolTest(unittest.TestCase):

    def test_sync(self):
        setting = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1a2s3dqwe'}
        pool = SyncConnectionPool(SyncMysql, setting, name='test sync pool', size=5, timeout=10)
        pool.create()

    def test_asyn(self):
        setting = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1a2s3dqwe'}
        self.pool = AsynConnectionPool(AsynMysql, setting, name='test asyn pool', size=5, timeout=10)
        ioloop.IOLoop.current().run_sync(self.pool.create)
        print(self.pool.get_connection())
        print 1
        time.sleep(100)
        # ioloop.IOLoop.instance().stop()

if __name__ == '__main__':
    unittest.main()
