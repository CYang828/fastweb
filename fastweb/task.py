# coding:utf8

"""消费者模块"""

import os
import sys
import json
from multiprocessing import Process

from fastweb import app
from fastweb.manager import Manager
from fastweb.util.tool import timing
from fastweb.exception import TaskError
from fastweb.component.task import Task
from fastweb.util.python import load_object
from fastweb.components import SyncComponents


__all__ = ['start_task_worker']
DEFAULT_TIMEOUT = 5


class IFaceWorker(object):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        pass

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        pass


class Worker(Task):
    """工作者类"""

    eattr = {'task_class': str, 'broker': str, 'queue': str, 'exchange': str, 'routing_key': str, 'backend': str}
    oattr = {'timeout': int}

    def __init__(self, setting):
        """初始化任务"""

        super(Worker, self).__init__(setting)

        import sys
        sys.path.append(os.getcwd())
        del sys

        # 设置执行任务的类
        self._task_cls = load_object(self.task_class)
        self._worker_obj = None

    def __str__(self):
        return '<Task: {name} of queue({queue}) exchange({exchange}) routing_key({routing_key})>'.\
            format(name=self.name, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)

    def run(self, *args, **kwargs):
        """任务处理
        转发给具体执行对象的run方法"""

        # Components中生成requestid
        self._worker_obj = type('Worker', (self._task_cls, SyncComponents, IFaceWorker), {})()
        self._worker_obj.requestid = self.request.id

        if hasattr(self._worker_obj, 'run'):
            self._worker_obj.recorder('IMPORTANT', '{obj} start\nRequest:\n{request}\nArgument: {args}\t{kwargs}'.format(obj=self,
                                                                                                                         request=json.dumps(self.request.as_execution_options(), indent=4),
                                                                                                                         args=args,
                                                                                                                         kwargs=kwargs))
            with timing('ms', 10) as t:
                ret = self._worker_obj.run(*args, **kwargs)
            self._worker_obj.recorder('IMPORTANT', '{obj} end\nReturn: {r} -- {t}'.format(obj=self, r=ret, t=t))
            return ret
        else:
            self._worker_obj.recorder('CRITICAL', '{obj} must have run function!'.format(obj=self))
            raise TaskError

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

        if hasattr(self._worker_obj, 'on_success'):
            self._worker_obj.recorder('INFO', '{obj} success callback start'.format(obj=self))
            with timing('ms', 10) as t:
                r = self._worker_obj.on_success(retval, task_id, args, kwargs)
            self._worker_obj.recorder('INFO', '{obj} success callback end -- {t}'.format(obj=self, t=t))
            return r

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

        self._worker_obj.recorder('ERROR', '{obj} failure\nTaskid: {id}\nException: {e}'.format(obj=self,
                                                                                                id=task_id,
                                                                                                e=exc))

        if hasattr(self._worker_obj, 'on_failure'):
            self._worker_obj.recorder('INFO', '{obj} failure callback start'.format(obj=self))
            with timing('ms', 10) as t:
                r = self._worker_obj.on_failure(exc, task_id, args, kwargs, einfo)
            self._worker_obj.recorder('INFO', '{obj} failure callback end -- {t}'.format(obj=self, t=t))
            return r

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

        if hasattr(self._worker_obj, 'on_retry'):
            self._worker_obj.recorder('INFO', '{obj} retry callback start'.format(obj=self))
            with timing('ms', 10) as t:
                self._worker_obj.on_retry(exc, task_id, args, kwargs, einfo)
            self._worker_obj.recorder('INFO', '{obj} retry callback end -- {t}'.format(obj=self, t=t))
        else:
            self._worker_obj.recorder('ERROR', '{obj} retry\nTaskid: {id}\nException: {e}'.format(obj=self,
                                                                                                  id=task_id,
                                                                                                  e=exc))

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

        if hasattr(self._worker_obj, 'after_return'):
            self._worker_obj.recorder('INFO', '{obj} after return callback start'.format(obj=self))
            with timing('ms', 10) as t:
                self._worker_obj.after_return(status, retval, task_id, args, kwargs, einfo)
            self._worker_obj.recorder('INFO', '{obj} after return callback end -- {t}'.format(obj=self, t=t))

        self._worker_obj.release()


def start_task_worker():
    """启动任务消费者

    每个application在一个进程中，不推荐定义大于CPU核数个application"""

    if not app.bRecorder:
        app.load_recorder()

    # 通过篡改命令行的参数更改application的node名称
    # 命令行中的-n参数会失效

    tasks = Manager.get_classified_components('worker')

    for task in tasks:
        argv = sys.argv
        argv.append('-n')
        argv.append('fastweb@celery@{app}'.format(app=task.name))
        p = Process(target=task.application.start, args=(argv,))
        p.start()
