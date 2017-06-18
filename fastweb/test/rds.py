# coding:utf8

import time
import unittest

import init
from fastweb.component.db.rds import SyncRedis


class MysqlTest(unittest.TestCase):

    def runTest(self):
        setting = {'host': 'localhost', 'port': 6379}
        redis = SyncRedis(setting).set_name('redis_test')
        redis.connect()

        # time.sleep(10)

        # 查询测试
        print(redis.query('settest_key test_val'))
        print(redis.query('keys *'))


if __name__ == '__main__':
    unittest.main()
