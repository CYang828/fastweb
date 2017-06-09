# coding:utf8

"""兼容模块"""

import sys


if sys.version_info < (3, 0):
    import ConfigParser as cParser
else:
    import configparser as cParser
