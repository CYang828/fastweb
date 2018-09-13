# encoding:utf-8

from functools import wraps

from fastweb.util.python import dict2sequence, list2sequence
from fastweb.accesspoint import coroutine
from fastweb.component.db.rds import SyncRedis, AsynRedis


class cache(object):
    def __init__(self, storage, key, expire=None):
        self._storage = storage
        self._storage_obj = None
        self._expire = expire
        self._key = key
        self._rkey = None

    def __call__(self, func):
        @coroutine
        @wraps(func)
        def wrapped_func(cls, *args):
            key = self._key.format(*args)
            storage = getattr(cls, self._storage)
            self._storage_obj = storage
            self._rkey = key
            if isinstance(self._storage_obj, AsynRedis):
                info = yield AsynCache.read(cls, self._storage_obj, key, func, args, self)
                return info
            elif isinstance(self._storage_obj, SyncRedis):
                SyncCache.read(cls, self._storage_obj, key, func, args, self)
        return wrapped_func

    @coroutine
    def update(self, data):
        if isinstance(self._storage_obj, AsynRedis):
            info = yield AsynCache.update(self._storage_obj, self._rkey, data)
            return info
        elif isinstance(self._storage_obj, SyncRedis):
            SyncCache.update(self._storage_obj, self._rkey, data)


class AsynCache(cache):

    @staticmethod
    @coroutine
    def read(cls, storage, key, fn, args, obj):
        """从缓存中读取"""
        ist = yield storage.query("EXISTS {}".format(key))
        if ist:
            _type = yield storage.query("TYPE {}".format(key))
            if _type == 'hash':
                info = yield storage.query("HGETALL {}".format(key))
                return info
            elif _type == 'list':
                info = yield storage.query("LRANGE {} 0 -1".format(key))
                return info
        else:
            r = yield fn(cls, *args, __cache__=obj)
            return r

    @staticmethod
    @coroutine
    def update(storage, key, data):
        """更新缓存"""

        if isinstance(data, dict):
            data_sequence = dict2sequence(data)
            yield storage.query("HMSET {} {}".format(key, data_sequence))
        elif isinstance(data, list):
            data_sequence = list2sequence(data)
            yield storage.query("LPUSH {} {}".format(key, data_sequence))


class SyncCache(object):

    @staticmethod
    def read(cls, storage, key, fn, args):
        ist = storage.query("EXISTS {}".format(key))
        if ist:
            info = storage.query("HGETALL {}".format(key))
            return info

    @staticmethod
    def update(cls, storage, key):
        """更新缓存"""
        pass




