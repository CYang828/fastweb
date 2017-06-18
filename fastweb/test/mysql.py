# coding:utf8

import time
import unittest

from fastweb import coroutine, ioloop
from fastweb.loader import app
from fastweb.component.db.mysql import SyncMysql, AsynMysql


app.load_recorder('app.log', system_log_path='sys.log', system_level='DEBUG')


class SyncMysqlTest(unittest.TestCase):

    def runTest(self):
        setting = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1a2s3dqwe'}
        mysql = SyncMysql(setting).set_name('sync_mysql_test')
        mysql.connect()

        # time.sleep(10)

        # 查询测试
        mysql.query('SELECT * FROM mysql.user;')
        print(mysql.fetch())

        # mysql.query('CREATE DATABASE fastweb;')
        mysql.query('CREATE TABLE IF NOT EXISTS fastweb.test (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,name VARCHAR(4) NOT NULL);')

        # mysql.query("INSERT INTO fastweb.test (name) values ('F');")

        # 事务测试
        mysql.start_event()
        mysql.exec_event("INSERT INTO fastweb.test (id, name) values (%s, %s);", (1113, 'Q'))
        mysql.end_event()

        #
        # mysql.rollback()
        # mysql.end_event()


class AsynMysqlTest(unittest.TestCase):

    @coroutine
    def asyn(self):
        setting = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1a2s3dqwe'}
        mysql = AsynMysql(setting).set_name('asyn_mysql_test')
        yield mysql.connect()

        # time.sleep(10)

        # 查询测试
        yield mysql.query('SELECT * FROM mysql.user;')
        print(mysql.fetch())

        # time.sleep(30)
        # kill 掉线程
        yield mysql.query('SELECT * FROM mysql.user;')

        yield mysql.start_event()
        yield mysql.exec_event("INSERT INTO fastweb.test (name) values ('Z');")
        yield mysql.end_event()
        print '+++++++++++++++++++++++++++++++++++++++++'

        yield mysql.query('SELECT * FROM mysql.user;')
        print(mysql.fetch())

    def runTest(self):
        ioloop.IOLoop.instance().run_sync(self.asyn)


if __name__ == '__main__':
    unittest.main()
