# coding:utf8

from fastweb.accesspoint import ioloop
from fastweb.component.db.mysql import SyncMysql, AsynMysql
from fastweb.pool import SyncConnectionPool, AsynConnectionPool


setting = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''}


class TestSyncPool(object):
    def test_create(self):
        pool = SyncConnectionPool(SyncMysql, setting, name='test sync mysql pool', size=5, awake=10)
        pool.create()

    def test_add_connection(self):
        pool = SyncConnectionPool(SyncMysql, setting, name='test sync mysql pool', size=5, awake=10)
        pool.create()
        pool.add_connection()

    def test_get_connection(self):
        pool = SyncConnectionPool(SyncMysql, setting, name='test sync mysql pool', size=5, awake=10)
        pool.create()
        assert isinstance(pool.get_connection(), SyncMysql)

    def test_rescue(self):
        pool = SyncConnectionPool(SyncMysql, setting, name='test sync mysql pool', size=5, awake=10)
        pool.create()
        pool.rescue()

    def test_concurrency_get_connection(self):
        """大并发下的获取连接"""
        pass

    def test_maxconn_rescue(self):
        """动态扩展到最大连接数"""
        pass


class TestAsynPool(object):
    def test_create(self):
        pool = AsynConnectionPool(AsynMysql, setting, name='test asyn pool', size=5, awake=10)
        ioloop.IOLoop.current().run_sync(pool.create)

    def test_add_connection(self):
        pool = AsynConnectionPool(AsynMysql, setting, name='test asyn pool', size=5, awake=10)
        ioloop.IOLoop.current().run_sync(pool.create)
        ioloop.IOLoop.current().run_sync(pool.add_connection)

    def test_get_connection(self):
        pool = AsynConnectionPool(AsynMysql, setting, name='test asyn pool', size=5, awake=10)
        ioloop.IOLoop.current().run_sync(pool.create)
        assert isinstance(pool.get_connection(), AsynMysql)

    def test_rescue(self):
        pool = AsynConnectionPool(AsynMysql, setting, name='test asyn pool', size=5, awake=10)
        ioloop.IOLoop.current().run_sync(pool.create)
        ioloop.IOLoop.current().run_sync(pool.rescue)

    def test_concurrency_get_connection(self):
        """大并发下的获取连接"""
        pass

    def test_maxconn_rescue(self):
        """动态扩展到最大连接数"""
        pass


