# coding:utf8

"""系统全局加载模块
外部调用想要影响fastweb行为,必须通过改模块中的方法
所有工作都是在启动前完成,外部导入全部使用全路径引用,防止错误的引入
"""

import json

from .accesspoint import ioloop

import fastweb.manager
from fastweb.util.tool import timing
from fastweb.accesspoint import AsyncHTTPClient
from fastweb.util.configuration import ConfigurationParser
from fastweb.util.log import setup_logging, getLogger, recorder, check_logging_level, set_record_color


__all__ = ['app']
DEFAULT_APP_LOG_PATH = 'fastweb@application.log'
DEFAULT_SYS_LOG_PATH = 'fastweb@system.log'


class Loader(object):
    """系统全局加载器
    """

    def __init__(self):
        # 配置系统
        self.configs = None
        self.configer = None
        self.component_configers = []

        # 日志系统
        self.system_recorder = None
        self.application_recorder = None

        # 系统错误码
        self.errcode = None

        # 日志是否被设置过
        self.bRecorder = False

        # 增加最大数据量
        AsyncHTTPClient.configure(None, max_body_size=1000000000)

    def load_recorder(self, application_log_path=DEFAULT_APP_LOG_PATH, system_log_path=DEFAULT_SYS_LOG_PATH,
                      logging_setting=None, application_level='DEBUG', system_level='DEBUG', logging_colormap=None):
        """加载日志对象

        需要最先加载,因为其他加载都需要使用recorder
        其他server启动时会默认加载一遍，用户没有特殊需求可以不加载

        :parameter:
          - `application_log_path`: 应用日志路径
          - `system_log_path`: 系统日志路径,默认系统日志路径和应用日志路径相同
          - `logging_setting_path`: 默认从fastweb.settting.default_logging.yaml获取配置,
                                    可以指定为自定义的日志配置,必须有application_recorder和system_recorder
          - `logging_setting`: 自定以logging配置
          - `application_level`: 应用日志输出级别
          - `system_level`: 系统日志输出级别
          - `logging_colormap`: 输出日志颜色
        """

        if not logging_setting:
            from fastweb.setting.default_logging import DEFAULT_LOGGING_SETTING
            logging_setting = DEFAULT_LOGGING_SETTING

        logging_setting['handlers']['application_file_time_handler']['filename'] = application_log_path
        logging_setting['handlers']['system_file_size_handler']['filename'] = system_log_path

        if application_level:
            check_logging_level(application_level)
            logging_setting['loggers']['application_recorder']['level'] = application_level

        if system_level:
            check_logging_level(system_level)
            logging_setting['loggers']['system_recorder']['level'] = system_level

        setup_logging(logging_setting)

        self.system_recorder = getLogger('system_recorder')
        self.application_recorder = getLogger('application_recorder')

        if logging_colormap:
            set_record_color(logging_colormap)

        self.bRecorder = True
        recorder('INFO',
                 'load recorder configuration\n{conf}\n\n'
                 'application log: {app_path} [{app_level}]\n'
                 'system log: {sys_path} [{sys_level}]'.format(conf=json.dumps(logging_setting, indent=4),
                                                               app_path=application_log_path,
                                                               app_level=application_level,
                                                               sys_path=system_log_path,
                                                               sys_level=system_level))

    def load_configuration(self, backend='ini', **setting):
        """加载配置文件

        :parameter:
          - `backend`: 配置方式,目前支持ini
          - `setting`: 该格式需要的设置参数
        """

        self.configer = ConfigurationParser(backend, **setting)
        self.configs = self.configer.configs

        recorder('INFO', 'load configuration\nbackend:\t{backend}\n'
                         'setting:\t{setting}\nconfiguration:\t{config}'.format(backend=backend,
                                                                                setting=setting,
                                                                                config=self.configs))

    def load_component(self, layout, backend='ini', **setting):
        """加载组件管理器

        可以进行多次加载

        :parameter:
          - `layout`: 当前调用的层次，web, service, task
          - `backend`: 配置方式,目前支持ini
          - `setting`: 该格式需要的设置参数
        """

        layout = layout.lower()
        configer = ConfigurationParser(backend, **setting)

        # 加载需要管理连接池的组件
        recorder('INFO', 'load connection component start')
        with timing('ms', 10) as t:
            if layout in ['service']:
                fastweb.manager.SyncConnManager.setup(configer)
            elif layout in ['web']:
                fastweb.manager.AsynConnManager.configer = configer
                ioloop.IOLoop.current().run_sync(fastweb.manager.AsynConnManager.setup)
        recorder('INFO', 'load connection component successful -- {time}'.format(time=t))

        # 加载不需要管理连接池的组件
        recorder('INFO', 'load component start')
        with timing('ms', 10) as t:
            fastweb.manager.Manager.setup(layout, configer)
        recorder('INFO', 'load component successful -- {time}'.format(time=t))
        self.component_configers.append(configer)
        return configer

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
