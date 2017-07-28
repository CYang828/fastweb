# coding:utf8


from fastweb import app
from fastweb.task import start_task_worker


class TestWorker(object):
    @staticmethod
    def test_start_worker():
        app.load_component(layout='task', backend='ini', path='config/worker.ini')
        start_task_worker()

if __name__ == '__main__':
    TestWorker.test_start_worker()

