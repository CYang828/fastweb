# coding:utf8

"""任务层模块"""

import sys
from multiprocessing import Process

from fastweb.component import Component
from fastweb.util.python import load_object
from fastweb.components import SyncComponents
from fastweb.accesspoint import CeleryTask, Celery, Ignore, Queue, Exchange


__all__ = ['Task']
applications = []


class Task(Component, CeleryTask, SyncComponents):
    """任务类"""

    eattr = {'name': str, 'task_class': str, 'broker': str, 'queue': str, 'exchange': str, 'routing_key': str}
    oattr = {'backend': str}

    def __init__(self, setting):
        """初始化任务"""

        super(Task, self).__init__(setting)
        SyncComponents.__init__(self)

        # 设置任务的属性
        self.name = self.setting['name']
        self._broker = self.setting['broker']
        self._task_class = self.setting['task_class']
        self._backend = self.setting.get('backend')
        exchange_type = self.setting.get('exchange_type', 'direct')

        # 设置绑定的application的属性
        app = Celery(main=self.name, broker=self._broker, backend=self._backend)
        app.tasks.register(self)

        # 设置任务的路由
        queue = Queue(name=self.queue, exchange=Exchange(name=self.exchange, type=exchange_type), routing_key=self.routing_key)
        app.conf.update(task_queues=(queue,),
                        task_routes={self.name: {'queue': self.queue, 'routing_key': self.routing_key}})

        # task和application绑定
        applications.append(app)
        self.application = app
        self.bind(app)

        # 设置执行任务的类
        task_obj = load_object(self._task_class)
        self._task_obj = task_obj()

    def __str__(self):
        return '<Task: {name} of {app} queue({queue}) exchange({exchange}) routing_key({routing_key})>'.\
            format(name=self.name, app=self.app, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)

    def run(self, *args, **kwargs):
        # 处理任务

        self._task_obj.run(*args, **kwargs)

    def on_success(self, retval, task_id, args, kwargs):
        # 任务成功回调

        if hasattr(self._task_obj, 'on_success'):
            self._task_obj.on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # 任务失败回调

        if hasattr(self._task_obj, 'on_failure'):
            self._task_obj.on_failure(exc, task_id, args, kwargs, einfo)
        else:
            raise exc

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        # 任务重试回调

        if hasattr(self._task_obj, 'on_retry'):
            self._task_obj.on_retry(exc, task_id, args, kwargs, einfo)
        else:
            raise exc

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        # 任务返回回调

        if hasattr(self._task_obj, 'after_return'):
            self._task_obj.on_retry(status, retval, task_id, args, kwargs, einfo)

    def call_asyn(self, *args, **kwargs):
        """异步调用"""

        self.recorder('INFO', 'asynchronous call {task} start'.format(task=self))
        taskid = self.apply_async(queue=self.queue, exchange=self.exchange, routing_key=self.routing_key, *args, **kwargs)
        self.recorder('INFO', 'asynchronous call {task} successful -- {taskid}'.format(task=self, taskid=taskid))

    def call(self, *args, **kwargs):
        """同步调用"""

        self.recorder('INFO', 'synchronize call {task} start'.format(task=self))
        result = self.apply(queue=self.queue, exchange=self.exchange, routing_key=self.routing_key, *args, **kwargs)
        self.recorder('INFO', 'synchronize call {task} successful -- {ret}'.format(task=self, ret=result))
        return result

    def call_delay(self):
        """延时调用"""
        pass


def start_task_worker():
    """启动任务消费者

    每个application在一个进程中"""

    # 通过篡改命令行的参数更改application的node名称
    # 命令行中的-n参数会失效

    for application in applications:
        argv = sys.argv
        argv.append('-n')
        argv.append('fastweb@celery@{app}'.format(app=application.main))
        p = Process(target=application.start, args=(argv,))
        p.start()
