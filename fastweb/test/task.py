# coding:utf8

from fastweb.accesspoint import ioloop, coroutine
from fastweb.component.task import AsynTask, SyncTask

setting = {'_name': 'task test',
           'broker': 'amqp://guest:guest@localhost:5672//',
           'backend': 'redis://localhost/0',
           'task_class': 'some_tasks.add.Add',
           'queue': 'test_task_queue',
           'exchange': 'test_task_exchange',
           'routing_key': 'test_task_routing_key'}


class TestAsynTask(object):
    def test_call(self):
        task = AsynTask(setting)

        @coroutine
        def _call():
            r = yield task.call((1, 2))
            assert r == 3
        ioloop.IOLoop.current().run_sync(_call)

    def test_call_async(self):
        task = AsynTask(setting)

        @coroutine
        def _call():
            r = yield task.call_async((1, 2))
            print(r)
        ioloop.IOLoop.current().run_sync(_call)


class TestSyncTask(object):
    def test_call(self):
        task = SyncTask(setting)
        assert task.call((1, 2)) == 3

    def test_call_async(self):
        task = SyncTask(setting)
        print((task.call_async((1, 2))))

