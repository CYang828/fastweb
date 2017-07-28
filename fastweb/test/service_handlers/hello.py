# coding:utf8

from fastweb.service import ABLogic


class HelloServiceHandler(ABLogic):

    def sayHello(self):
        print 'sayHello'
