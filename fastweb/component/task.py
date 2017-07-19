# coding:utf8

"""任务模块"""

from fastweb.spec import torcelery
from fastweb.util.tool import timing
from fastweb.component import Component
from fastweb.exception import TaskError
from fastweb.accesspoint import CeleryTask, Celery, Queue, Exchange, coroutine, Return


DEFAULT_TIMEOUT = 5


class Task(Component, CeleryTask):
    """任务类"""

    eattr = {'task_class': str, 'broker': str, 'queue': str, 'exchange': str, 'routing_key': str, 'backend': str}
    oattr = {'timeout': int}

    def __init__(self, setting):
        """初始化任务"""

        Component.__init__(self, setting)
        CeleryTask.__init__(self)

        # 设置任务的属性
        self.name = setting['_name']
        exchange_type = self.setting.get('exchange_type', 'direct')
        self.timeout = self.setting.get('timeout', DEFAULT_TIMEOUT)
        self.requestid = None

        # 设置绑定的application的属性
        app = Celery(main=self.name, broker=self.broker, backend=self.backend)
        app.tasks.register(self)
        self.backend = app.backend

        # 设置任务的路由
        queue = Queue(name=self.queue, exchange=Exchange(name=self.exchange, type=exchange_type), routing_key=self.routing_key)
        app.conf.update(task_queues=(queue,),
                        task_routes={self.name: {'queue': self.queue, 'routing_key': self.routing_key}})

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
            self.recorder('INFO', 'synchronize call {task} start\nArgument: {args} {kwargs}'.format(obj=self,
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

        self.recorder('INFO', 'synchronize call {obj} successful -- {ret} -- {t}'.format(obj=self,
                                                                                         ret=result,
                                                                                         t=t))
        raise Return(result)
