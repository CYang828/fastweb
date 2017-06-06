# coding:utf8

"""框架运行模式模块"""

from collections import namedtuple


Pattern = namedtuple('Pattern', 'quantization describe')
SyncPattern = Pattern(quantization=1, describe='sync pattern')
AsynPattern = Pattern(quantization=2, describe='asyn pattern')
