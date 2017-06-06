# coding:utf8


import unittest

from fastweb.loader import app
from fastweb import SyncPattern, AsynPattern


class LoaderTest(unittest.TestCase):
    def test_sync(self):
        # app.load_recorder('log/app.log')
        # app.load_recorder('log/app.log', system_log_path='log/sys.log')
        # app.load_errcode()
        # app.system_recorder.debug('recorder test')
        app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')
        app.load_configuration(path='config/config.ini')
        app.load_manager(pattern=SyncPattern)

    def test_asyn(self):
        app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')
        app.load_configuration(path='config/config.ini')
        app.load_manager(pattern=AsynPattern)


if __name__ == '__main__':
    unittest.main()
