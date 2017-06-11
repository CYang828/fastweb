# coding:utf8

import unittest

from fastweb.loader import app
from fastweb.util.process import FProcess

app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')


class FProcessTest(unittest.TestCase):

    def task(self):
        import time
        time.sleep(10)

    def runTest(self):
        process = FProcess(name='test', task=self.task)
        process.start()
        print 111111
        process.stop()


if __name__ == '__main__':
    unittest.main()
