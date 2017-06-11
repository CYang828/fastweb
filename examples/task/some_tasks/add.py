# coding:utf8

import time


class Add(object):

    def run(self, x, y):
        print 'worker'
        print '啊啊啊啊啊啊啊啊'
        print self
        print x+y
        time.sleep(5)
        return x+y


