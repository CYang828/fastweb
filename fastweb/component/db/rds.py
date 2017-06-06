# coding:utf8

import redis
import shlex
import tornadis
from tornado.locks import Condition
from tornadis.exceptions import ConnectionError
from redis.exceptions import ConnectionError, TimeoutError, ResponseError

from fastweb.accesspoint import coroutine, Return

import fastweb.util.tool as tool
from fastweb.exception import RedisError
from fastweb.component import Component


DEFAULT_DB = 0
DEFAULT_PORT = 6379
DEFAULT_TIMEOUT = 5
DEFAULT_CHARSET = 'utf8'


class SyncRedis(Component):
    """同步redis
       线程不安全"""

    eattr = {'host': str}
    oattr = {'port': int, 'password': str, 'db': int, 'timeout': int, 'charset': str}

    def __init__(self, setting):
        self.db = DEFAULT_DB
        self.port = DEFAULT_PORT
        self.timeout = DEFAULT_TIMEOUT
        self.charset = DEFAULT_CHARSET

        super(SyncRedis, self).__init__(setting)

        self.isConnect = False
        self._client = None

    def __str__(self):
        return '<SyncRedis {name} {host} {port} {db} {charset}>'.format(
            name=self.name, host=self.host, port=self.port, db=self.db, charset=self.charset)

    def connect(self):
        """建立连接"""

        self.host = self.setting.get('host')
        assert self.host, '`host` is essential of redis'
        self.port = int(self.setting.get('port', DEFAULT_PORT))
        self.db = int(self.setting.get('db', 0))
        self.password = self.setting.get('password')
        self.timeout = int(self.setting.get('timeout', DEFAULT_TIMEOUT))
        self.charset = self.setting.get('charset', DEFAULT_CHARSET)

        self.setting = {'host': self.host,
                        'port': self.port,
                        'password': self.password,
                        'db': self.db,
                        'socket_timeout': self.timeout,
                        'charset': self.charset}

        try:
            self.recorder('INFO', '{obj} connect start'.format(obj=self))
            self._client = redis.StrictRedis()
            self.set_idle()
            self.isConnect = True
            self.recorder('INFO', '{obj} connect successful'.format(obj=self))
        except ConnectionError as e:
            self.recorder('ERROR', '{obj} connect failed [{msg}]'.format(obj=self, msg=e))
            self.isConnect = False
            raise RedisError

    def query(self, command):
        """命令行操作
           ConnectionError可能是超出连接最大数
           TimeoutError可能是连接不通"""

        try:
            cmd = shlex.split(command)
            self.recorder('INFO', '{obj} query start\n{cmd}'.format(obj=self, cmd=command))
            with tool.timing('s', 10) as t:
                response = self._client.execute_command(*cmd)
            self.recorder('INFO', '{obj} query successful\n{cmd} -- {time}'.format(obj=self, cmd=command, time=t))
        except (ConnectionError, TimeoutError) as e:
            # redis内部对这两种异常进行了重试操作
            self.recorder('ERROR', '{obj} connection error [{msg}]'.format(obj=self, msg=e))
            raise RedisError
        except ResponseError as e:
            self.recorder('ERROR', '{obj} query error [{msg}]'.format(obj=self, msg=e))
            raise RedisError

        return self._parse_response(response)

    @staticmethod
    def _parse_response(response):
        """解析response"""

        if response == 'OK':
            return True
        else:
            return response


class AsynRedis(Component):
    """异步redis组件"""

    def __init__(self, **kwargs):
        self.rebuild(kwargs)

    @coroutine
    def rebuild(self, kwargs):
        super(AsynRedis, self).__init__()

        self._redis = None

        self.host = kwargs.get('host')
        assert self.host, '`host` is essential of redis'
        self.port = kwargs.get('port', DEFAULT_PORT)
        self.password = kwargs.get('password', None)
        self.timeout = kwargs.get('timeout', DEFAULT_TIMEOUT)
        self.db = kwargs.get('db', 0)

        self.redis_config = {'host': self.host,
                             'port': int(self.port),
                             'password': self.password,
                             'connect_timeout': int(self.timeout),
                             'autoconnect': True,
                             'db': int(self.db)}

        self._connect_condition = Condition()

        try:
            self.set_idle()
            self._redis = tornadis.Client(**self.redis_config)
            yield self._redis.connect()
            self._connect_condition.notify()
        except ConnectionError as ex:
            self.set_error(ex)

    def __str__(self):
        return '<AsynRedis {host} {port} {name}>'.format(
            host=self.host, port=self.port, name=self.name)

    @coroutine
    def call(self, *args, **kwargs):
        """执行redis命令"""

        if not self._redis.is_connected:
            yield self._connect_condition.wait()

        if self._redis.is_connected:
            with tool.timing('s', 10) as t:
                future = yield self._redis.call(*args, **kwargs)
            self._logger('INFO', 'Redis Command [{command}] -- [{time}]'.format(command=' '.join(str(v) for v in args), time=t))
            raise Return(future)
