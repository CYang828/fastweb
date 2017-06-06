# coding:utf8

import pprint
import pymongo
from pymongo import MongoClient
from motor import motor_tornado
from tornado.gen import coroutine, Return
from pymongo.errors import ConnectionFailure

import fastweb.util.tool as tool
from fastweb.util.python import dumps
from fastweb.exception import MongoError
from fastweb.component import Component


DEFAULT_PORT = 27017
DEFAULT_TIMEOUT = 5


class Mongo(Component):
    """Mongo组件基类"""

    eattr = {'host': str}
    oattr = {'port': int, 'user': str, 'password': str, 'db': str, 'timeout': int}

    def __init__(self, setting):
        self.port = DEFAULT_PORT
        self.timeout = DEFAULT_TIMEOUT

        super(Mongo, self).__init__(setting)

        self.isConnect = False
        self._client = None
        self._db = None
        self._response = None

        self._prepare()

    def _prepare(self):
        self.host = 'mongodb://{user}:{password}@{host}'.format(user=self.user, password=self.password, host=self.host) if self.user and self.password else 'mongodb://{host}'.format(host=self.host)
        self.setting['host'] = self.host
        self.setting.pop('db', None)
        self.setting.pop('user', None)
        self.setting.pop('password', None)
        self.setting['connectTimeoutMS'] = self.setting.pop('timeout', None)

    def connect(self):
        raise NotImplementedError

    def select_db(self, db):
        """选择数据库"""

        try:
            self.recorder('INFO', '{obj} select database [{db}]'.format(obj=self, db=db))
            self._db = getattr(self._client, db)
        except AttributeError as e:
            self.recorder('ERROR', '{obj} select database error [msg]'.format(obj=self, msg=e))
            raise MongoError

    def query(self):
        raise NotImplementedError

    @staticmethod
    def _parse_response(response):
        """解析response
           结果为空时fisrtBatch中为空列表
           TODO:不知道什么时候ok返回非1值"""

        if response['ok']:
            return response['cursor']['firstBatch']
        return response

    def print_response(self):
        """打印返回值,调试使用"""

        pprint.pprint(self._response)

    def error(self):
        self.isConnect = False


class SyncMongo(Mongo):
    """"同步mongo
        线程不安全
    """

    def __str__(self):
        return '<SyncMongo {name} {host} {port} {db}>'.format(
            name=self.name, host=self.host, port=self.port, db=self.db)

    def connect(self):
        """建立连接"""

        try:
            self.recorder('INFO', '{obj} connect start'.format(obj=self))
            self.set_idle()
            self._client = MongoClient(**self.setting)
            if self.db:
                self.select_db(self.db)
            self.isConnect = True
            self.recorder('INFO', '{obj} connect successful'.format(obj=self))
        except ConnectionFailure as e:
            self.recorder('ERROR', '{obj} connect failed [{msg}]'.format(obj=self, msg=e))
            self.error()
            raise MongoError
        return self

    def query(self, command, value=1, check=True, allowable_errors=None, **kwargs):
        """命令行操作
           pymongo内部没有实现重试,需要进行重试
           TODO:对不同的异常做不同的操作"""

        if not self._db:
            self.recorder('CRITICAL', 'please select db first!')

        shell_command = 'db.runCommand(\n{cmd}\n)'.format(cmd=dumps(command, indent=4, whole=4))
        self.recorder('INFO', '{obj} command start\n{cmd}'.format(obj=self, cmd=shell_command))
        try:
            with tool.timing('s', 10) as t:
                response = self._db.command(command=command, value=value, check=check, allowable_errors=allowable_errors, **kwargs)
        except pymongo.errors.PyMongoError as e:
            self.recorder('ERROR', '{obj} command error [{msg}]'.format(obj=self, msg=e))
            raise MongoError
        self.recorder('INFO', '{obj} command successful\n{cmd} -- {time}'.format(obj=self, cmd=shell_command, time=t))

        self._response = self._parse_response(response)
        return self._response


class AsynMongo(Mongo):
    """异步Mongo组件"""

    def __str__(self):
        return '<AsynMongo {host} {port} {name}>'.format(
            host=self.host, port=self.port, name=self.name)

    @coroutine
    def connect(self):
        """建立连接"""

        try:
            self.recorder('INFO', '{obj} connect start'.format(obj=self))
            self.set_idle()
            self._client = motor_tornado.MotorClient(**self.setting)
            if self.db:
                self.select_db(self.db)
            self.isConnect = True
            self.recorder('INFO', '{obj} connect successful'.format(obj=self))
        except ConnectionFailure as e:
            self.recorder('ERROR', '{obj} connect failed [{msg}]'.format(obj=self, msg=e))
            self.error()
            raise MongoError
        raise Return(self)

    @coroutine
    def query(self, command, value=1, check=True, allowable_errors=None, **kwargs):
        """命令行操作
           pymongo内部没有实现重试,需要进行重试
           TODO:对不同的异常做不同的操作"""

        if not self._db:
            self.recorder('CRITICAL', 'please select db first!')

        shell_command = 'db.runCommand(\n{cmd}\n)'.format(cmd=dumps(command, indent=4, whole=4))
        self.recorder('INFO', '{obj} command start\n{cmd}'.format(obj=self, cmd=shell_command))
        try:
            with tool.timing('s', 10) as t:
                response = yield self._db.command(command=command, value=value, check=check,
                                                  allowable_errors=allowable_errors, **kwargs)
        except pymongo.errors.PyMongoError as e:
            self.recorder('ERROR', '{obj} command error [{msg}]'.format(obj=self, msg=e))
            raise MongoError
        self.recorder('INFO', '{obj} command successful\n{cmd} -- {time}'.format(obj=self, cmd=shell_command, time=t))

        self._response = self._parse_response(response)
        raise Return(self._response)
