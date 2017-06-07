# coding:utf8

"""Mysql模块"""

import pymysql
import tornado_mysql

from fastweb.accesspoint import iostream
from fastweb.accesspoint import coroutine, Return

import fastweb.util.tool as tool
from fastweb.component import Component
from fastweb.exception import MysqlError
from fastweb.util.tool import Retry, RetryPolicy

DEFAULT_PORT = 3306
DEFAULT_TIMEOUT = 5
DEFAULT_CHARSET = 'utf8'
DEFAULT_AUTOCOMMIT = True


class Mysql(Component):
    """Mysql基类"""

    eattr = {'host': str}
    oattr = {'port': int, 'user': str, 'password': str, 'db': str, 'timeout': int, 'charset': str, 'autocommit': bool}

    def __init__(self, setting):
        self.port = DEFAULT_PORT
        self.charset = DEFAULT_CHARSET
        self.timeout = DEFAULT_TIMEOUT
        self.autocommit = DEFAULT_AUTOCOMMIT

        super(Mysql, self).__init__(setting)

        self._conn = None
        self._cur = None
        # 事务标识
        self._event = False

        # 最后执行sql
        self._sql = None
        # 最后执行sql参数
        self._args = None

        self._prepare()

    def _prepare(self):
        """准备工作"""
        self.setting['passwd'] = self.setting.pop('password', None)
        self.setting['connect_timeout'] = self.setting.pop('timeout', None)

    def _format_sql(self, sql, args):
        """格式化sql
        占位符不需要严格区分类型，%s是一个好的选择"""

        def type_convert(v):
            if v is None:
                return 'NULL'
            return v

        if isinstance(args, dict):
            self._args = args = {k: type_convert(v) for k, v in args.items()}
            self._sql = sql % args
        elif isinstance(args, tuple):
            self._args = args = tuple([type_convert(v) for v in args])
            self._sql = sql % args
        elif isinstance(args, str):
            self._sql = sql % args
        else:
            self._sql = sql

        return sql

    def connect(self):
        """建立连接"""
        raise NotImplementedError

    def ping(self):
        """维持长连接"""
        raise NotImplementedError

    def reconnect(self):
        """重新建立连接"""
        raise NotImplementedError

    def start_event(self):
        """开始事务"""
        raise NotImplementedError

    def exec_event(self, sql, **kwargs):
        """执行事务"""
        raise NotImplementedError

    def end_event(self):
        """结束事务
        如果不结束,则事务无效果,事务虽然无效但是会占用自增id
        """

        raise NotImplementedError

    def query(self, sql, **kwargs):
        """查询sql"""
        raise NotImplementedError

    def fetch(self):
        """获取一条结果"""
        return self._cur.fetchone()

    def fetchall(self):
        """获取全部结果"""
        return self._cur.fetchall()

    def close(self):
        """关闭连接"""
        raise NotImplementedError

    def rollback(self):
        """事务回滚"""
        raise NotImplementedError

    def commit(self):
        """事务提交"""
        raise NotImplementedError

    @property
    def efficetid(self):
        """返回effectid"""
        return int(self._conn.insert_id())

    @property
    def threadid(self):
        """返回服务端线程id"""
        return int(self._conn.thread_id())


class SyncMysql(Mysql):
    """同步mysql
       线程不安全"""

    def __str__(self):
        return '<SyncMysql|{name}|{id} {host} {port} {user} {db} {charset}>'.format(
            id=id(self),
            host=self.host,
            port=self.port,
            user=self.user,
            db=self.db,
            name=self.name,
            charset=self.charset)

    def connect(self):
        """建立连接"""

        try:
            self.recorder('INFO', '{obj} connect start'.format(obj=self))
            self._conn = pymysql.connect(**self.setting)
            self.recorder('INFO', '{obj} connect successful ({threadid})'.format(obj=self, threadid=self._conn.server_thread_id[0]))
        except pymysql.Error as e:
            self.recorder('ERROR', '{obj} connect failed [{msg}]'.format(obj=self, msg=e))
            raise MysqlError

        return self

    def ping(self):
        """保持连接"""

        try:
            self.recorder('INFO', '{obj} ping start'.format(obj=self))
            self._conn.ping()
            self.recorder('INFO', '{obj} ping successful'.format(obj=self))
        except pymysql.Error as e:
            self.recorder('WARN', '{obj} ping error [{msg}]'.format(obj=self, msg=e))
            raise MysqlError

    def reconnect(self):
        """重新连接"""

        try:
            self.recorder('WARN', '{obj} reconnect start'.format(obj=self))
            self.connect()
            self._cur = None
            self.recorder('WARN', '{obj} reconnect successful'.format(obj=self))
        except pymysql.Error as e:
            self.recorder('ERROR', '{obj} reconnect error [{msg}]'.format(msg=e))
            raise MysqlError

        return self

    def start_event(self):
        """事务开始"""

        try:
            self._event = True
            self.recorder('INFO', '{obj} start event'.format(obj=self))
            self._conn.begin()
        except pymysql.OperationalError as e:
            self.recorder('WARN', '{obj} event start error [{msg}]'.format(msg=e))
            self.reconnect()
            self.start_event()

    def exec_event(self, sql, args=None):
        """事务执行"""

        if self._event:
            self.recorder('INFO', '{obj} execute event'.format(obj=self))
            return self.query(sql, args)
        else:
            self.recorder('CRITICAL', 'please start event first!')
            raise MysqlError

    def end_event(self):
        """事务结束"""

        if self._event:
            self._event = False
            self.recorder('INFO', '{obj} end event'.format(obj=self))
            self.commit()
        else:
            self.recorder('CRITICAL', 'please start event first! ')
            raise MysqlError

    def query(self, sql, args=None):
        """查询sql"""

        # 执行过程中的重试,只重试一次
        mysql_retry_policy = RetryPolicy(times=1, error=MysqlError)
        Retry(self, '{obj}'.format(obj=self), self._query, sql, mysql_retry_policy, args).run_sync()

    def _query(self, sql, retry, args):

        if not self._cur:
            self._cur = self._conn.cursor(pymysql.cursors.DictCursor)
        elif self._cur and not self._event:
            self._cur.close()
            self._cur = self._conn.cursor(pymysql.cursors.DictCursor)

        try:
            self._format_sql(sql, args)

            self.recorder('INFO', '{obj} query start ({threadid})\n{sql}'.format(obj=self, threadid=self._conn.server_thread_id[0], sql=self._sql))
            with tool.timing('s', 10) as t:
                self._cur.execute(sql, args)
            self.recorder('INFO',
                          '{obj} query successful\n{sql}\t[{time}]\t[{effect}]'.format(obj=self, sql=self._sql, time=t,
                                                                                       effect=self._cur.rowcount))
        except pymysql.OperationalError as e:
            self.recorder('ERROR', '{obj} mysql has gone away [{msg}]'.format(obj=self, msg=e))
            self.reconnect()
            raise retry
        except (pymysql.IntegrityError, pymysql.ProgrammingError) as e:
            self.recorder('ERROR', '{obj} query error\n{sql}\n[{msg}]'.format(obj=self, sql=self._sql, msg=e))
            raise MysqlError
        except (KeyError, TypeError) as e:
            self.recorder('ERROR',
                          '{obj} sql format error\n{sql}\n{args}\n[{msg}]'.format(obj=self, sql=sql, args=args,
                                                                                  msg=e))
            raise MysqlError

        if not self._event:
            self.commit()

        return self._cur.rowcount

    def close(self):
        """关闭连接"""

        self.recorder('INFO', '{obj} connection close start'.format(obj=self))
        self._cur.close()
        self._conn.close()
        self.recorder('INFO', '{obj} connection close successful'.format(obj=self))

    def rollback(self):
        """回滚"""

        # TODO:记录本次事务语句
        self._conn.rollback()
        self.recorder('INFO', '{obj} query rollback'.format(obj=self))

    def commit(self):
        """事务提交"""

        self._conn.commit()
        self.recorder('INFO', '{obj} query commit'.format(obj=self))


class AsynMysql(Mysql):
    """异步mysql组件"""

    def __str__(self):
        return '<AsynMysql|{name}|{id} {host} {port} {user} {db} {charset}>'.format(
            id=id(self),
            host=self.host,
            port=self.port,
            user=self.user,
            db=self.db,
            name=self.name,
            charset=self.charset)

    @coroutine
    def connect(self):
        """建立连接"""

        try:
            self.recorder('INFO', '{obj} connect start'.format(obj=self))
            self._conn = yield tornado_mysql.connect(**self.setting)
            self.recorder('INFO', '{obj} connect successful ({threadid})'.format(obj=self, threadid=self._conn.server_thread_id[0]))
        except tornado_mysql.Error as e:
            self.recorder('ERROR', '{obj} connect error [{msg}]'.format(obj=self, msg=e))
            raise MysqlError

        raise Return(self)

    @coroutine
    def ping(self):
        """维持连接"""

        try:
            self.recorder('WARN', '{obj} ping start'.format(obj=self))
            yield self._conn.ping()
            self.recorder('WARN', '{obj} ping successful'.format(obj=self))
        except tornado_mysql.Error as e:
            self.recorder('WARN', '{obj} ping error [{msg}]'.format(obj=self, msg=e))
            raise MysqlError

    @coroutine
    def reconnect(self):
        """重新连接"""

        try:
            self.recorder('WARN', '{obj} reconnect start'.format(obj=self))
            yield self.connect()
            self._cur = None
            self.recorder('WARN', '{obj} reconnect successful'.format(obj=self))
        except tornado_mysql.Error as e:
            self.recorder('ERROR', '{obj} reconnect error [{msg}]'.format(obj=self, msg=e))
            raise MysqlError

        raise Return(self)

    @coroutine
    def start_event(self):
        """事务开始"""

        try:
            self._event = True
            self.recorder('INFO', '{obj} start event'.format(obj=self))
            yield self._conn.begin()
        except tornado_mysql.OperationalError as e:
            self.recorder('WARN', '{obj} event start error [{msg}]'.format(obj=self, msg=e))
            yield self.reconnect()
            yield self.start_event()

    @coroutine
    def exec_event(self, sql, args=None):
        """事务执行"""

        if self._event:
            self.recorder('INFO', '{obj} execute event'.format(obj=self))
            rows = yield self.query(sql, args)
            raise Return(rows)
        else:
            self.recorder('CRITICAL', 'please start event first!')
            raise MysqlError

    @coroutine
    def end_event(self):
        """事务结束"""

        if self._event:
            self._event = False
            self.recorder('INFO', '{obj} end event'.format(obj=self))
            yield self.commit()
        else:
            self.recorder('CRITICAL', 'please start event first! ')
            raise MysqlError

    @coroutine
    def query(self, sql, args=None):
        """查询sql"""

        mysql_retry_policy = RetryPolicy(times=1, error=MysqlError)
        effect = yield Retry(self, '{obj}'.format(obj=self), self._query, sql, mysql_retry_policy, args).run_asyn()
        raise Return(effect)

    @coroutine
    def _query(self, sql, retry, args=None):
        if not self._cur:
            self._cur = self._conn.cursor(tornado_mysql.cursors.DictCursor)
        elif self._cur and not self._event:
            self._cur.close()
            self._cur = self._conn.cursor(tornado_mysql.cursors.DictCursor)

        try:
            self._format_sql(sql, args)

            self.recorder('INFO', '{obj} query start ({threadid})\n{sql}'.format(obj=self,
                          threadid=self._conn.server_thread_id[0], sql=sql))
            with tool.timing('ms', 10) as t:
                yield self._cur.execute(sql, args)
            self.recorder('INFO',
                          '{obj} query successful\n{sql}\t[{time}]\t[{effect}]'.format(obj=self, sql=sql, time=t,
                                                                                       effect=self._cur.rowcount))
        except (tornado_mysql.OperationalError, tornado_mysql.InterfaceError, iostream.StreamClosedError) as e:
            self.recorder('ERROR', '{obj} mysql has gone away [{msg}]'.format(obj=self, msg=e))
            yield self.reconnect()
            raise retry
        except (tornado_mysql.IntegrityError, tornado_mysql.ProgrammingError) as e:
            self.recorder('ERROR', '{obj} query error\n{sql}\n[{msg}]'.format(obj=self, sql=sql, msg=e))
            raise MysqlError
        except (KeyError, TypeError) as e:
            self.recorder('ERROR',
                          '{obj} sql format error\n{sql}\n{args}\n[{msg}]'.format(obj=self, sql=sql, args=args,
                                                                                  msg=e))
            raise MysqlError

        if not self._event:
            yield self.commit()

        raise Return(self._cur.rowcount)

    @coroutine
    def rollback(self):
        """回滚"""

        yield self._conn.rollback()

    @coroutine
    def commit(self):
        """提交操作"""

        yield self._conn.commit()

    @coroutine
    def close(self):
        """关闭连接"""

        yield self._cur.close()
        yield self._conn.close()
