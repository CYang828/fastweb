# coding:utf8

from fastweb.accesspoint import ioloop
from fastweb.component.rpc.tft import AsynTftRpc, SyncTftRpc

sync_setting = {'host': 'localhost', 'port': 7777, 'thrift_module': 'fastweb.test.fastweb_thrift_sync.HelloService.HelloService'}
asyn_setting = {'host': 'localhost', 'port': 7777, 'thrift_module': 'fastweb.test.fastweb_thrift_async.HelloService.HelloService'}


class TestSyncThrift(object):
    def test_connect(self):
        rpc = SyncTftRpc(sync_setting).set_name('test sync thrift')
        rpc.connect()
        rpc.close()

    def test_call(self):
        rpc = SyncTftRpc(sync_setting).set_name('test sync thrift')
        rpc.connect()
        assert rpc.sayHello() == 'hello'
        rpc.close()


class TestAsynThrift(object):
    def test_connect(self):
        rpc = AsynTftRpc(asyn_setting).set_name('test asyn thrift')
        ioloop.IOLoop.current().run_sync(rpc.connect)
        rpc.close()

    def test_call(self):
        rpc = AsynTftRpc(asyn_setting).set_name('test asyn thrift')
        ioloop.IOLoop.current().run_sync(rpc.connect)
        assert ioloop.IOLoop.current().run_sync(rpc.sayHello) == 'hello'
        rpc.close()

