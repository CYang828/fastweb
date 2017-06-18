# coding:utf8

import unittest

from fastweb.loader import app
from fastweb.service import start_service_server


app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')


class ServiceTest(unittest.TestCase):

    def runTest(self):
        start_service_server('config/service.ini')


if __name__ == '__main__':
    unittest.main()
