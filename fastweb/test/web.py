# coding:utf8

import unittest


from fastweb import ioloop
from fastweb.loader import app
from fastweb.web import AsyncHTTPClient, Request, coroutine


app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='DEBUG')


class AsynComponentTest(unittest.TestCase):

    @coroutine
    def do(self):

        request = Request(method='GET', url='http://www.baidu.com')
        response = yield AsyncHTTPClient().fetch(request)
        print response.body

    def runTest(self):
        ioloop.IOLoop.instance().run_sync(self.do)


if __name__ == '__main__':
    unittest.main()
