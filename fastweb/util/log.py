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
COLORMAP = {
    'INFO': 'white',
    'DEBUG': 'green',
    'WARN': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'magenta',
    'IMPORTANT': 'cyan'
}


def setup_logging(setting):
    """加载logging配置

    :parameter:
      - `setting`:配置"""

    global bSetupLogging
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
        from fastweb import app
        app.load_recorder()
        setup_logging(DEFAULT_LOGGING_SETTING)

    rec = fastweb.loader.app.system_recorder if fastweb.loader.app.system_recorder else getLogger('system_recorder')
    record(level, msg, rec)


def set_record_color(colormap):
    global COLORMAP
    if colormap.keys() in LOGGING_LEVEL:
        COLORMAP = colormap
    else:
        recorder('CRITICAL', 'colormap invalid, please fill it like {colormap}'.format(colormap=str(COLORMAP)))


def record(level, msg, r, extra=None):
    global COLORMAP
    level = level.upper()
    check_logging_level(level)

    if level == 'ERROR':
        msg = '{msg}\n\n{exeinfo}'.format(msg=msg, exeinfo=traceback.format_exc(), whole=4)

    logger_color = COLORMAP.get(level, 'white')
    logger_func = getattr(r, level.lower())
    logger_func(colored(msg, logger_color, attrs=['bold']), extra=extra)


def check_logging_level(level):
    """检查日志级别是否正确

    :parameter:
      - `level`:日志级别"""

    if level not in LOGGING_LEVEL:
        recorder('CRITICAL', 'please check logging level! right options {levels}, current level is {level}'.format(level=level,
                                                                                                                    levels=str(LOGGING_LEVEL)))
        raise ParameterError
