# coding:utf8

"""连接池模块"""

import json
import threading
from Queue import Queue, Empty

from accesspoint import coroutine, ioloop, Return

from fastweb.util.log import recorder
from fastweb.util.thread import FThread

DEFAULT_TIMEOUT = 80000
DEFAULT_MAXCONN = 500


class ConnectionPool(object):
    """连接池"""

    def __init__(self, cls, setting, size, name, awake=DEFAULT_TIMEOUT, maxconnections=DEFAULT_MAXCONN):
        """设置连接池

        连接池创建时尽量早的报错,运行过程中尽量去修复错误

        :parameter:
          - `cls`:连接池中实例化的类
          -`setting`:参数
          -`size`:连接池大小
          -`name`:连接池名字
          -`timeout`:连接最大超时时间,尝试重连时间
        """

        self._cls = cls
        self._pool = Queue()
        self._name = name
        self._size = int(size)
        self._pattern = None
        self._timeout = int(awake) if awake else DEFAULT_TIMEOUT
        self._setting = setting
        self._used_pool = []
        self._unused_pool = []
        self._maxconnections = int(maxconnections) if maxconnections else DEFAULT_MAXCONN
        self._lock = threading.Lock()
        self._rescue_thread = None

    def remove_connection(self, connection):
        """移除连接"""
        pass

    def lend_connection(self, timeout):
        """租用连接

        :parameter:
          `timeout`:租用时间,超过租用时间自动归还
        """
        pass

    def return_connection(self, connection):
        """归还连接

        :parameter:
          - `connection`:连接"""

        self._used_pool.remove(connection)
        self._unused_pool.append(connection)
        self._pool.put_nowait(connection)
        recorder('DEBUG',
                 '<{name}> return connection {conn}, total connections {count}'.format(name=self._name, conn=connection,
                                                                                       count=self._pool.qsize()))

    def rescue(self):
        """独立线程进行连接恢复"""

        raise NotImplementedError


class SyncConnectionPool(ConnectionPool):
    def __str__(self):
        return '<{name}|SyncConnectionPool>'.format(name=self._name)

    def _create_connection(self):
        """创建连接"""

        return self._cls(self._setting).set_name(self._name).connect()

    def add_connection(self):
        """同步增加连接"""

        connection = self._create_connection()
        self._pool.put_nowait(connection)
        self._unused_pool.append(connection)

    def create(self):
        """同步创建连接池"""

        recorder('DEBUG', 'synchronize connection pool create start <{name}>\n{setting}'.format(name=self._name,
                                                                                                setting=json.dumps(
                                                                                                    self._setting,
                                                                                                    indent=4)))
        for _ in range(self._size):
            self.add_connection()
        self.rescue()
        recorder('DEBUG', 'synchronize connection pool create successful <{name}>'.format(name=self._name))

    def rescue(self):
        self._rescue_thread = FThread(name='rescue', task=self._rescue, period=self._timeout)
        self._rescue_thread.start()

    def _rescue(self, thread):
        """同步恢复连接
        目前先全量恢复
        """

        recorder('INFO', '{thread} <{name}> rescue connection start'.format(thread=thread, name=self._name))
        for conn in self._unused_pool:
            conn.ping()
        recorder('INFO', '{thread} <{name}> rescue connection successful'.format(thread=thread, name=self._name))

    def get_connection(self):
        """获取连接"""

        try:
            self._lock.acquire()
            connection = self._pool.get(block=True)
            self._unused_pool.remove(connection)
            self._lock.release()
        except Empty:
            connection = self._create_connection()
            recorder('WARN', '<{name}> connection pool is empty,create a new connection {conn}'.format(name=self._name,
                                                                                                       conn=connection))

        self._used_pool.append(connection)
        recorder('DEBUG', '{obj} get connection {conn} {id}, left connections {count}'.format(obj=self, conn=connection,
                                                                                              id=id(connection),
                                                                                              count=self._pool.qsize()))
        return connection


class AsynConnectionPool(ConnectionPool):
    def __str__(self):
        return '<{name}|AsynConnectionPool>'.format(name=self._name)

    @coroutine
    def _create_connection(self):
        """创建连接"""

        connection = yield self._cls(self._setting).set_name(self._name).connect()
        raise Return(connection)

    @coroutine
    def create(self):
        """异步创建连接池"""

        recorder('DEBUG', 'asynchronous connection pool create start <{name}>\n{setting}'.format(name=self._name,
                                                                                                 setting=json.dumps(
                                                                                                     self._setting,
                                                                                                     indent=4)))
        for _ in range(self._size):
            yield self.add_connection()
        self.rescue()
        recorder('DEBUG', 'asynchronous connection pool create successful <{name}>'.format(name=self._name))

    @coroutine
    def add_connection(self):
        """同步增加连接"""

        connection = yield self._create_connection()
        self._pool.put_nowait(connection)
        self._unused_pool.append(connection)

    def rescue(self):
        """异步恢复连接
        目前全量恢复
        """

        def on_reconnect(future):
            if future.exception:
                print future.exc_info

        def on_rescue():
            recorder('INFO', '<{name}> rescue connection start'.format(name=self._name))
            for conn in self._unused_pool:
                future = conn.ping()
                ioloop.IOLoop.current().add_future(future, on_reconnect)
            recorder('INFO', '<{name}> rescue connection successful'.format(name=self._name))
            self.rescue()

        ioloop.IOLoop.current().add_timeout(ioloop.IOLoop.current().time() + self._timeout, on_rescue)

    def _scale(self, thread):
        recorder('WARN', '{thread} {obj} scale connection pool start'.format(thread=thread, obj=self))
        scale_loop = ioloop.IOLoop(make_current=True)
        scale_loop.run_sync(self.create)
        recorder('WARN', '{thread} {obj} scale connection pool successful'.format(thread=thread, obj=self))
        scale_loop.start()

    def scale_connections(self):
        scale_thread = FThread(name='scale', task=self._scale)
        scale_thread.start()
        scale_thread.join()

    def get_connection(self):
        """获取连接"""

        # TODO:连接池扩展机制问题
        try:
            self._lock.acquire()
            connection = self._pool.get(block=True)
            self._unused_pool.remove(connection)
            self._lock.release()
            if self._pool.qsize() < 2:
                self.scale_connections()
        except Empty:
            recorder('CRITICAL',
                     '<{name}> connection pool is empty,please use service to separate your database operation'.format(
                         name=self._name))
            raise

        self._used_pool.append(connection)
        recorder('DEBUG', '{obj} get connection {conn} {id}, left connections {count}'.format(obj=self, conn=connection,
                                                                                              id=id(connection),
                                                                                              count=self._pool.qsize()))
        return connection
