# coding:utf8

import unittest

from fastweb import ioloop
from fastweb import coroutine
from fastweb.loader import app
from fastweb.component.db.mongo import SyncMongo, AsynMongo


app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')


class SyncMongoTest(unittest.TestCase):

    def runTest(self):

        setting = {'host': 'localhost', 'db': 'local'}
        mongo = SyncMongo(setting).set_name('mongo_test')
        mongo.connect()

        mongo.query({'find': 'startup_log'})
        mongo.print_response()

        # print(mongo.query('show dbs'))


class AsynMongoTest(unittest.TestCase):

    @coroutine
    def q(self):
        setting = {'host': 'localhost', 'db': 'local', 'port': 27017}
        self.mongo = AsynMongo(setting).set_name('mongo_test')
        yield self.mongo.connect()
        yield self.mongo.query({'find': 'startup_log'})
        self.mongo.print_response()

    def runTest(self):
        ioloop.IOLoop.instance().run_sync(self.q)


if __name__ == '__main__':
    unittest.main()
