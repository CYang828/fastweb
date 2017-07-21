# coding;utf8


from fastweb.accesspoint import ioloop, coroutine
from fastweb.component.db.mysql import SyncMysql, AsynMysql


setting = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''}


class TestSyncMysql(object):
    def test_connect(self):
        mysql = SyncMysql(setting).set_name('sync_mysql_test')
        mysql.connect()

    def test_query(self):
        mysql = SyncMysql(setting).set_name('sync_mysql_test')
        mysql.connect()
        assert mysql.query('select * from mysql.user;')
        assert mysql.fetch()


class TestAsynMysql(object):
    def test_connect(self):
        mysql = AsynMysql(setting).set_name('asyn_mysql_test')
        ioloop.IOLoop.instance().run_sync(mysql.connect)

    def test_query(self):
        mysql = AsynMysql(setting).set_name('asyn_mysql_test')
        ioloop.IOLoop.instance().run_sync(mysql.connect)

        @coroutine
        def _query():
            ret = yield mysql.query('select * from mysql.user;')
            assert ret

        ioloop.IOLoop.instance().run_sync(_query)
