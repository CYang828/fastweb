# coding:utf8

import logging
import traceback
import logging.config
from logging import getLogger

from termcolor import colored

import fastweb
from fastweb.exception import ParameterError
from fastweb.setting.default_logging import DEFAULT_LOGGING_SETTING


bSetupLogging = False
LOGGING_LEVEL = ['INFO',
                 'DEBUG',
                 'WARN',
                 'ERROR',
                 'CRITICAL',
                 'IMPORTANT']


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
        setup_logging(DEFAULT_LOGGING_SETTING)

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
