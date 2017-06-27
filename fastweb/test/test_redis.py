# coding:utf8


from fastweb.accesspoint import ioloop, coroutine
from fastweb.component.db.rds import SyncRedis, AsynRedis


setting = {'host': 'localhost'}


class TestSyncRedis(object):

    def test_connect(self):
        redis = SyncRedis(setting)
        redis.connect()

    def test_query(self):
        redis = SyncRedis(setting)
        redis.connect()
        assert redis.query('set name jackson')


class TestAsynRedis(object):

    def test_connect(self):
        redis = AsynRedis(setting)
        ioloop.IOLoop.current().run_sync(redis.connect)

    def test_query(self):
        redis = AsynRedis(setting)
        ioloop.IOLoop.current().run_sync(redis.connect)

        @coroutine
        def _query():
            r = yield redis.query('set name jackson')
            assert r
        ioloop.IOLoop.current().run_sync(_query)
