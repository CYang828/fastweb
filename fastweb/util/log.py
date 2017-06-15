# coding:utf8

import os
import logging
import traceback
import logging.config
from logging import getLogger

import yaml
from termcolor import colored

import fastweb
from fastweb.exception import ParameterError


bSetupLogging = False
LOGGING_LEVEL = ['INFO',
                 'DEBUG',
                 'WARN',
                 'ERROR',
                 'CRITICAL',
                 'IMPORTANT']

DEFAULT_YAML_LOGGING_EVN = 'YAML_LOG_CFG'
DEFAULT_YAML_LOGGING_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'setting/default_logging.yaml'))


def get_yaml_logging_setting(path=DEFAULT_YAML_LOGGING_PATH, env_key=DEFAULT_YAML_LOGGING_EVN):
    """从yaml文件中获取logging配置

    先从环境变量env_key获取配置文件,如果不存在则从path中获取配置文件

    :parameter:
      - `path`:yaml文件路径
      - `env_key`:yaml配置环境变量,默认为YAML_LOG_CFG"""

    setting = None
    value = os.getenv(env_key, None)
    path = value if value else path

    if os.path.exists(path):
        with open(path, 'rt') as f:
            setting = yaml.safe_load(f.read())

    return setting


def setup_logging(setting):
    """加载logging配置

    :parameter:
      - `setting`:配置"""

    logging.config.dictConfig(setting)
    bSetupLogging = True


def recorder(level, msg):
    """日志记录

    load_recorder后会使用系统的日志handler,没有load_recorder会使用logging默认handler

    :parameter:
      - `level`:日志级别
      - `msg`:日志信息
    """

    if not bSetupLogging:
        setup_logging(get_yaml_logging_setting())

    rec = fastweb.loader.app.system_recorder if fastweb.loader.app.system_recorder else getLogger('system_recorder')
    record(level, msg, rec)


def record(level, msg, r, extra=None):
    level = level.upper()
    level_dict = {
        'INFO': (r.info, 'white'),
        'DEBUG': (r.debug, 'green'),
        'WARN': (r.warn, 'yellow'),
        'ERROR': (r.error, 'red'),
        'CRITICAL': (r.critical, 'magenta'),
        'IMPORTANT': (r.info, 'cyan')
    }
    check_logging_level(level)

    if level == 'error':
        msg = '{msg}\n\n{exeinfo}'.format(msg=msg, exeinfo=traceback.format_exc(), whole=4)

    logger_func, logger_color = level_dict[level]
    logger_func(colored(msg, logger_color, attrs=['bold']), extra=extra)


def check_logging_level(level):
    """检查日志级别是否正确

    :parameter:
      - `level`:日志级别"""

    if level not in LOGGING_LEVEL:
        recorder('CRITICAL', 'please check logging level! right options {levels}'.format(levels=str(LOGGING_LEVEL)))
        raise ParameterError
