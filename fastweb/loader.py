# coding:utf8

"""系统全局加载模块
外部调用想要影响fastweb行为,必须通过改模块中的方法
所有工作都是在启动前完成,外部导入全部使用全路径引用,防止错误的引入
"""

import json

from accesspoint import ioloop

import fastweb.manager
from fastweb.util.tool import timing
from fastweb.exception import FastwebException
from fastweb.pattern import SyncPattern, AsynPattern
from fastweb.util.configuration import Configuration
from fastweb.util.log import setup_logging, getLogger, recorder, check_logging_level


__all__ = ['app', 'SyncPattern', 'AsynPattern']


class Loader(object):
    """系统全局加载器
    """

    def __init__(self):
        # 配置系统
        self.configs = None
        self.configer = None

        # 日志系统
        self.system_recorder = None
        self.application_recorder = None

        # 管理系统
        self.pattern = None

        # 系统错误码
        self.errcode = None

    def load_recorder(self, application_log_path, system_log_path=None, logging_setting_path=None, logging_setting=None,
                      application_level='DEBUG', system_level='DEBUG'):
        """加载日志对象

        需要最先加载,因为其他加载都需要使用recorder

        :parameter:
          - `app_log_path`: 应用日志路径
          - `system_log_path`: 系统日志路径,默认系统日志路径和应用日志路径相同
          - `logging_setting_path`: 默认从fastweb.settting.default_logging.yaml获取配置,可以指定为自定义的日志配置,必须有application_recorder和system_recorder
          - `logging_setting`: 自定以logging配置
          - `application_level`: 应用日志输出级别
          - `system_level`: 系统日志输出级别
        """

        # TODO:配色自定义
        if not logging_setting:
            from fastweb.setting.default_logging import DEFAULT_LOGGING_SETTING
            logging_setting = DEFAULT_LOGGING_SETTING

        logging_setting['handlers']['application_file_time_handler']['filename'] = application_log_path
        logging_setting['handlers']['system_file_size_handler']['filename'] = system_log_path if system_log_path else application_log_path

        if application_level:
            check_logging_level(application_level)
            logging_setting['loggers']['application_recorder']['level'] = application_level

        if system_level:
            check_logging_level(system_level)
            logging_setting['loggers']['system_recorder']['level'] = system_level

        setup_logging(logging_setting)

        self.system_recorder = getLogger('system_recorder')
        self.application_recorder = getLogger('application_recorder')

        recorder('INFO',
                 'load recorder configuration\n{conf}\n\napplication log: {app_path} [{app_level}]\nsystem log: {sys_path} [{sys_level}]'.format(
                     conf=json.dumps(logging_setting, indent=4), app_path=application_log_path,
                     app_level=application_level, sys_path=system_log_path, sys_level=system_level))

    def load_configuration(self, backend='ini', **setting):
        """加载配置文件,组件配置文件

        :parameter:
          - `backend`: 配置方式,目前支持ini
          - `setting`: 该格式需要的设置参数
        """

        if not self.system_recorder and not self.application_recorder:
            recorder('CRITICAL', 'please load recorder first!')
            raise FastwebException

        self.configer = Configuration(backend, **setting)
        self.configs = self.configer.configs

        recorder('INFO', 'load configuration\nbackend:\t{backend}\nsetting:\t{setting}'.format(backend=backend,
                                                                                               setting=setting))

    def load_component(self, pattern, backend='ini', **setting):
        """加载组件管理器

        需要在load_configuration后进行

        :parameter:
          - `pattern`:同步或异步模式,SyncPattern或者AsynPattern
        """

        if not self.system_recorder and not self.application_recorder:
            recorder('CRITICAL', 'please load recorder first!')
            raise FastwebException

        self.pattern = pattern
        configer = Configuration(backend, **setting)

        # 加载需要管理连接池的组件
        recorder('INFO', 'load connection component start')
        with timing('ms', 10) as t:
            if pattern is SyncPattern:
                fastweb.manager.SyncConnManager.setup(configer)
            elif pattern is AsynPattern:
                fastweb.manager.AsynConnManager.configer = configer
                ioloop.IOLoop.current().run_sync(fastweb.manager.AsynConnManager.setup)
        recorder('INFO', 'load connection component successful -- {time}'.format(time=t))

        # 加载不需要管理连接池的组件
        recorder('INFO', 'load component start')
        with timing('ms', 10) as t:
            fastweb.manager.Manager.setup(configer)
        recorder('INFO', 'load component successful -- {time}'.format(time=t))

    def load_errcode(self, errcode=None):
        """加载系统错误码

        :parameter:
          - `errcode`:自定义错误码
        """

        if errcode:
            self.errcode = errcode
        else:
            from fastweb.setting.default_errcode import ERRCODE
            self.errcode = ERRCODE

        recorder('INFO', 'load errcode\n{errcode}'.format(errcode=json.dumps(self.errcode, indent=4)))
        return self.errcode


app = Loader()
