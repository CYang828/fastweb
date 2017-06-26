# coding:utf8

from fastweb import app
from fastweb.manager import Manager, SyncConnManager, AsynConnManager


class TestManager(object):

    def test_setup(self):
        configer = app.load_component('web', backend='ini', path='config/service.ini')
        Manager.setup(configer)


class TestSyncManager(object):

    def test_setup(self):
        configer = app.load_component('web', backend='ini', path='config/service.ini')
        SyncConnManager.setup(configer)


class TestAsynManager(object):

    def test_setup(self):
        configer = app.load_component('web', backend='ini', path='config/service.ini')
        AsynConnManager.setup(configer)


