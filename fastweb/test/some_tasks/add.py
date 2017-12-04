# coding:utf8

import time


class Add(object):

    def run(self, x, y):
        print('worker')
        print('啊啊啊啊啊啊啊啊')
        print(self)
        print((x+y))
        time.sleep(3)
        return(x+y)



