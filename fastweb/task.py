# coding:utf8

"""任务层模块"""

import sys
from multiprocessing import Process

from fastweb import torcelery
from fastweb.manager import Manager
from fastweb.util.tool import timing
from fastweb.component import Component
from fastweb.util.python import load_object
from fastweb.components import SyncComponents
from fastweb.accesspoint import CeleryTask, Celery, Ignore, Queue, Exchange, coroutine, Return


__all__ = ['start_task_worker']


class Task(Component, CeleryTask, SyncComponents):
    """任务类"""

    eattr = {'name': str, 'task_class': str, 'broker': str, 'queue': str, 'exchange': str, 'routing_key': str, 'backend': str}

    def __init__(self, setting):
        """初始化任务"""

        super(Task, self).__init__(setting)
        SyncComponents.__init__(self)

        # 设置任务的属性
        self.name = self.setting['name']
        self._broker = self.setting['broker']
        self._task_class = self.setting['task_class']
        self._backend = self.setting['backend']
        exchange_type = self.setting.get('exchange_type', 'direct')

        # 设置绑定的application的属性
        app = Celery(main=self.name, broker=self._broker, backend='redis://localhost')
        app.tasks.register(self)
        self.backend = app.backend

        # 设置任务的路由
        queue = Queue(name=self.queue, exchange=Exchange(name=self.exchange, type=exchange_type), routing_key=self.routing_key)
        app.conf.update(task_queues=(queue,),
                        task_routes={self.name: {'queue': self.queue, 'routing_key': self.routing_key}})

        # task和application绑定
        self.application = app
        self.bind(app)

        # 设置执行任务的类
        task_obj = load_object(self._task_class)
        self._task_obj = task_obj()

    def __str__(self):
        return '<Task: {name} of {app} queue({queue}) exchange({exchange}) routing_key({routing_key})>'.\
            format(name=self.name, app=self.app, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)

    def run(self, *args, **kwargs):
        """任务处理
        转发给具体执行对象的run方法"""

        return self._task_obj.run(*args, **kwargs)

    def on_success(self, retval, task_id, args, kwargs):
        """
        任务成功回调函数转发

        Run by the worker if the task executes successfully.

        Arguments:
            retval (Any): The return value of the task.
            task_id (str): Unique id of the executed task.
            args (Tuple): Original arguments for the executed task.
            kwargs (Dict): Original keyword arguments for the executed task.

        Returns:
            None: The return value of this handler is ignored.
        """

        if hasattr(self._task_obj, 'on_success'):
            return self._task_obj.on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        任务失败回调函数转发

        This is run by the worker when the task fails.

        Arguments:
            exc (Exception): The exception raised by the task.
            task_id (str): Unique id of the failed task.
            args (Tuple): Original arguments for the task that failed.
            kwargs (Dict): Original keyword arguments for the task that failed.
            einfo (~billiard.einfo.ExceptionInfo): Exception information.

        Returns:
            None: The return value of this handler is ignored.
        """

        if hasattr(self._task_obj, 'on_failure'):
            return self._task_obj.on_failure(exc, task_id, args, kwargs, einfo)
        else:
            raise exc

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试回调函数转发

        This is run by the worker when the task is to be retried.

        Arguments:
            exc (Exception): The exception sent to :meth:`retry`.
            task_id (str): Unique id of the retried task.
            args (Tuple): Original arguments for the retried task.
            kwargs (Dict): Original keyword arguments for the retried task.
            einfo (~billiard.einfo.ExceptionInfo): Exception information.

        Returns:
            None: The return value of this handler is ignored.
        """

        if hasattr(self._task_obj, 'on_retry'):
            self._task_obj.on_retry(exc, task_id, args, kwargs, einfo)
        else:
            raise exc

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """任务返回回调函数转发

        Arguments:
            status (str): Current task state.
            retval (Any): Task return value/exception.
            task_id (str): Unique id of the task.
            args (Tuple): Original arguments for the task.
            kwargs (Dict): Original keyword arguments for the task.
            einfo (~billiard.einfo.ExceptionInfo): Exception information.

        Returns:
            None: The return value of this handler is ignored.
        """

        if hasattr(self._task_obj, 'after_return'):
            self._task_obj.on_retry(status, retval, task_id, args, kwargs, einfo)

    @coroutine
    def call_async(self, *args, **kwargs):
        """异步调用"""

        with timing('ms', 10) as t:
            self.recorder('INFO', 'asynchronous call {task} start'.format(task=self))
            taskid = yield torcelery.async(self, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key, *args, **kwargs)
        self.recorder('INFO', 'asynchronous call {task} successful -- {taskid} -- {t}'.format(task=self, taskid=taskid, t=t))
        raise Return(taskid)

    @coroutine
    def call(self, *args, **kwargs):
        """同步调用"""

        # TODO:多个同步任务的链式调用
        with timing('ms', 10) as t:
            self.recorder('INFO', 'synchronize call {task} start'.format(task=self))
            result = yield torcelery.sync(self, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key, *args, **kwargs)
        self.recorder('INFO', 'synchronize call {task} successful -- {ret} -- {t}'.format(task=self, ret=result, t=t))
        raise Return(result)


def start_task_worker():
    """启动任务消费者

    每个application在一个进程中，不推荐定义大于CPU核数个application"""

    # 通过篡改命令行的参数更改application的node名称
    # 命令行中的-n参数会失效

    tasks = Manager.get_classified_components('task')

    for task in tasks:
        argv = sys.argv
        argv.append('-n')
        argv.append('fastweb@celery@{app}'.format(app=task.name))
        p = Process(target=task.application.start, args=(argv,))
        p.start()
