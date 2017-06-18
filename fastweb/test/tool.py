# coding:utf8


import unittest

import init
from fastweb.util.tool import Retry, RetryPolicy


class HelloError(Exception):
    pass


class RetryTest(unittest.TestCase):

    def runTest(self):

        policy = RetryPolicy(3, HelloError, interval=3, delay=2)

        policy1 = RetryPolicy(4, HelloError)

        def hello(time):
            print time
            raise policy

        def hello1(time):
            print time
            raise policy1

        retry = Retry('hello', hello, 1)
        retry.run()

        retry1 = Retry('hello1', hello1, 1)
        retry1.run()
