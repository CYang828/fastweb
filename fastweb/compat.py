# coding:utf8

"""兼容模块"""

import os
import sys


if sys.version_info < (3, 0):
    import configparser as cParser
    from urllib import urlencode, unquote
else:
    import configparser as cParser
    from urllib.parse import urlencode, unquote

if os.name == 'posix' and sys.version_info < (3, 0):
    import subprocess32 as subprocess
else:
    import subprocess



