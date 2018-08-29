# coding:utf8

"""任务模块"""

import json

import fastweb
from fastweb.loader import app
from fastweb.spec import torcelery
from fastweb.util.tool import timing
from fastweb.component import Component
from fastweb.exception import TaskError
from fastweb.accesspoint import CeleryTask, Celery, RMQueue, Exchange, coroutine, Return, crontab

from celery.loaders.base import BaseLoader


DEFAULT_TIMEOUT = 5


class TaskLoader(BaseLoader):
    """worker子进程创建后"""

    def on_worker_process_init(self):
        """worker子进程创建后，利用 `copy-on-write` 为每一个进程创建属于自己的连接池"""

        for configer in app.component_configers:
            fastweb.manager.SyncConnManager.setup(configer)


class Task(Component, CeleryTask):
    """任务类"""

    eattr = {'broker': str, 'queue': str, 'exchange': str, 'routing_key': str, 'backend': str}
    oattr = {'name': str, 'timeout': int, 'exchange_type': str, 'minute': str, 'hour': str,
             'day_of_week': str, 'day_of_month': str, 'month_of_year': str, 'concurrency': int}

    def __init__(self, setting):
        """初始化任务"""

        Component.__init__(self, setting)
        CeleryTask.__init__(self)

        # 设置任务的属性
        self.name = setting.get('name', setting['_name'])
        self.exchange_type = setting.get('exchange_type', 'direct')
        self.timeout = self.setting.get('timeout', DEFAULT_TIMEOUT)
        rate_limit = self.setting.get('rate_limit', None)
        acks_late = self.setting.get('acks_late', None)
        self.requestid = None
        # 设置跟踪任务启动状态，为了让异步访问时可以准确知道任务被执行了
        self.track_started = True

        # 定时任务
        minute = setting.get('minute', '*')
        hour = setting.get('hour', '*')
        day_of_week = setting.get('day_of_week', '*')
        day_of_month = setting.get('day_of_month', '*')
        month_of_year = setting.get('month_of_year', '*')

        # 设置绑定的application的属性
        app = Celery(main=self.name, loader=TaskLoader, broker=self.broker, backend=self.backend)
        app.tasks.register(self)
        self.backend = app.backend

        beat_schedule = {}
        if minute is not '*' or hour is not '*' or day_of_week is not '*' \
                or day_of_month is not '*' or month_of_year is not '*':
            beat_schedule = {
                                'timer_schedule':
                                {
                                    'task': self.name,
                                    'schedule': crontab(hour=hour, minute=minute, day_of_week=day_of_week, day_of_month=day_of_month, month_of_year=month_of_year),
                                },
                              }
        self.recorder('DEBUG', 'setup crontab {cron}'.format(cron=beat_schedule))

        # 设置任务的路由
        queue = RMQueue(name=self.queue, exchange=Exchange(name=self.exchange, type=self.exchange_type), routing_key=self.routing_key)
        app.conf.update(task_queues=(queue,),
                        task_routes={self.name: {'queue': self.queue, 'routing_key': self.routing_key}},
                        task_annotations={self.name: {'rate_limit': rate_limit}},
                        task_acks_late=acks_late,
                        beat_schedule=beat_schedule,
                        worker_concurrency=setting.get('concurrency', 1))

        # task和application绑定
        self.application = app
        self.bind(app)


class SyncTask(Task):
    """同步任务类"""

    def __str__(self):
        return '<SyncTask: {name} of queue({queue}) exchange({exchange}) routing_key({routing_key})>'.\
            format(name=self.name, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)

    def call_async(self, *args, **kwargs):
        """异步调用"""
        self.requestid = self.owner.requestid if self.owner else None
        with timing('ms', 10) as t:
            self.recorder('INFO', 'asynchronous call {obj} start'.format(obj=self))
            # 调用task层时，调用方的requestid会成为本次任务的taskid， 任务的requesid也为透传id
            taskid = self.apply_async(task_id=self.requestid,
                                      queue=self.queue,
                                      exchange=self.exchange,
                                      routing_key=self.routing_key,
                                      *args,
                                      **kwargs)
        self.recorder('INFO', 'asynchronous call {obj} successful -- {t}'.format(obj=self, t=t))
        return taskid

    def call(self, *args, **kwargs):
        """同步调用"""
        # TODO:多个同步任务的链式调用
        self.requestid = self.owner.requestid if self.owner else None
        with timing('ms', 10) as t:
            self.recorder('INFO', 'synchronize call {task} start'.format(task=self))
            # 调用task层时，调用方的requestid会成为本次任务的taskid， 任务的requesid也为透传id
            result = self.apply_async(task_id=self.requestid,
                                      queue=self.queue,
                                      exchange=self.exchange,
                                      routing_key=self.routing_key,
                                      *args,
                                      **kwargs)

            while True:
                if result.ready():
                    break

        if not result:
            self.recorder('ERROR',
                          'synchronize call {obj} timeout -- {t}'.format(obj=self, ret=result, t=t))
            raise TaskError

        self.recorder('INFO', 'synchronize call {obj} successful -- {ret} -- {t}'.format(obj=self,
                                                                                         ret=result,
                                                                                         t=t))
        return result.result


class AsynTask(Task):
    """异步任务类"""
    def __str__(self):
        return '<AsynTask: {name} of queue({queue}) exchange({exchange}) routing_key({routing_key})>'.\
            format(name=self.name, queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)

    @coroutine
    def call_async(self, *args, **kwargs):
        """异步调用"""
        self.requestid = self.owner.requestid if self.owner else None
        with timing('ms', 10) as t:
            self.recorder('INFO', 'asynchronous call {obj} start\nArgument: {args} {kwargs}'.format(obj=self,
                                                                                                    args=args,
                                                                                                    kwargs=kwargs))
            # 调用task层时，调用方的requestid会成为本次任务的taskid， 任务的requesid也为透传id
            taskid = yield torcelery.async(self,
                                           task_id=self.requestid,
                                           queue=self.queue,
                                           exchange=self.exchange,
                                           routing_key=self.routing_key,
                                           *args,
                                           **kwargs)
        self.recorder('INFO', 'asynchronous call {obj} successful -- {t}'.format(obj=self, t=t))
        raise Return(taskid)

    @coroutine
    def call(self, *args, **kwargs):
        """同步调用"""
        self.requestid = self.owner.requestid if self.owner else None
        # TODO:多个同步任务的链式调用
        with timing('ms', 10) as t:
            self.recorder('INFO', 'synchronize call {obj} start\nArgument: {args} {kwargs}'.format(obj=self,
                                                                                                   args=args,
                                                                                                   kwargs=kwargs))
            # 调用task层时，调用方的requestid会成为本次任务的taskid， 任务的requesid也为透传id
            result = yield torcelery.sync(self, self.timeout,
                                          task_id=self.requestid,
                                          queue=self.queue,
                                          exchange=self.exchange,
                                          routing_key=self.routing_key,
                                          *args,
                                          **kwargs)

        if not result:
            self.recorder('ERROR',
                          'synchronize call {obj} timeout -- {t}'.format(obj=self, ret=result, t=t))
            raise TaskError

        self.recorder('INFO', 'synchronize call {obj} successful\n'
                              'Return:{ret} -- {t}'.format(obj=self,
                                                           ret=result,
                                                           t=t))
        raise Return(result)
