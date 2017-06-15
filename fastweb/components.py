# coding:utf8

"""组件工具模块"""

import types
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor

import fastweb.loader
import fastweb.manager
from fastweb.accesspoint import HTTPClient
from fastweb.util.tool import uniqueid, timing
from fastweb.util.log import record, getLogger, recorder
from fastweb.exception import ComponentError, SubProcessError, HttpError


class Components(object):
    """组件基类
    基础组件功能
    """

    _blacklist = ['requestid', '_new_cookie', 'include_host',
                  '_active_modules', '_current_user', '_locale',
                  '__header__', 'priority', 'delivery_mode', 'compression', 'immediate', 'mandatory']
    executor = None

    def __init__(self):
        self.loader = fastweb.loader.app
        self.errcode = fastweb.loader.app.errcode
        self.configs = fastweb.loader.app.configs

        # 组件缓冲池,确保同一请求对同一组件只获取一次
        self._components = {}

    def __getattr__(self, name):
        """获取组件

        :parameter:
          - `name`: 组件名称
        """

        if name in self._blacklist:
            recorder('WARN', '{attr} in blacklist'.format(attr=name))
            raise AttributeError

        # 缓冲池中存在则使用缓冲池中的组件
        component = self._components.get(name)

        if not component:
            component = fastweb.manager.Manager.get_component(name, self)

            if not component:
                self.recorder('ERROR', "can't acquire idle component <{name}>".format(name=name))
                raise ComponentError

            self._components[name] = component
            self.recorder('DEBUG', '{obj} get component from manager {name} {com}'.format(obj=self, name=name, com=component))
            return component
        else:
            self.recorder('DEBUG', '{obj} get component from components cache {name} {com}'.format(obj=self, name=name, com=component))
            return component

    @staticmethod
    def gen_requestid():
        """生成requestid"""

        return uniqueid()

    def load_executor(self, size):
        """加载当前handler级别的线程池"""

        self.executor = ThreadPoolExecutor(size)

    def add_blacklist(self, attr):
        """增加类属性黑名单

        :parameter:
          - `attr`:属性名称
        """

        self._blacklist.append(attr)

    def add_function(self, **kwargs):
        """增加方法到对象中"""

        # TODO:有没有更好的加载方式
        for callname, func in kwargs.items():
            setattr(self, '{callname}'.format(callname=callname), types.MethodType(func, self))

    def recorder(self, level, msg):
        """日志记录

        :parameter:
          - `level`:日志登记
          - `msg`:记录信息
        """

        record(level, msg, getLogger('application_recorder'), extra={'requestid': self.requestid})

    def release(self):
        """释放组件"""

        for name, component in self._components.items():
            fastweb.manager.Manager.return_component(name, component)
            self.recorder('DEBUG', '{com} return manager'.format(com=component))

        self._components.clear()
        self.recorder('INFO', 'release all used components')


class SyncComponents(Components):
    """同步组件类"""

    def http_request(self, request):
        """http请求

        :parameter:
          - `request`:http请求
        """

        if hasattr(self, 'requestid'):
            _recorder = self.recorder
        else:
            _recorder = recorder

        _recorder('INFO', 'http request start {request}'.format(request=request))

        with timing('ms', 10) as t:
            try:
                response = HTTPClient().fetch(request)
            except HttpError as ex:
                _recorder('ERROR', 'http request error {request} {e}'.format(request=request, e=ex))
                raise HttpError

        _recorder('INFO', 'http request successful\n{response} -- {time}'.format(response=response.code, time=t))
        return response

    def call_subprocess(self, command, stdin_data=None):
        """命令行调用

        :parameter:
          - `command`:命令行
          - `stdin_data`:传入数据
        """

        if hasattr(self, 'requestid'):
            _recorder = self.recorder
        else:
            _recorder = recorder

        _recorder('INFO', 'call subprocess start\n{cmd}'.format(cmd=command))

        with timing('ms', 10) as t:
            sub_process = subprocess.Popen(shlex.split(command),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
            try:
                result, error = sub_process.communicate(stdin_data)
            except (OSError, ValueError) as ex:
                _recorder('ERROR', 'call subprocess\n({cmd}) ({e}) '.format(
                    cmd=command, e=ex, msg=result.strip() if result else error.strip()))
                raise SubProcessError

        if sub_process.returncode != 0:
            _recorder('ERROR', 'call subprocess error ({cmd}) <{time}> {msg}'.format(
                cmd=command, time=t, msg=result.strip() if result else error.strip()))
            raise SubProcessError

        _recorder('INFO', 'call subprocess successful\n{cmd}\n{msg}\n<{time}>'.format(
            cmd=command, time=t, msg=result.strip() if result else error.strip()))
        return result, error

