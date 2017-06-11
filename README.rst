Fastweb - 高速迭代 · 快速试错
============================

依赖 ``Tornado`` ``Celery`` ``Thrift`` 开发的快速构建web应用的框架。

Web层示例
--------

.. code-block:: ini

    ;组件配置文件(component.ini)

    ;thrift rpc 组件配置
    [tftrpc:hello_service]
    host = localhost
    port = 8888
    thrift_module = gen-py-tornado.HelloService.HelloService
    size = 10

    ;mysql组件配置
    [mysql:test_mysql]
    host = localhost
    port = 3306
    user = username
    password = password
    db = db_name
    timeout = 5
    charset=utf8
    size=5
    awake = 300

    ;mongo组件配置
    [mongo:test_mongo]
    host = localhost
    port = 27017
    timeout = 10

    ;redis组件配置
    [redis:test_redis]
    host = localhost
    port = 6379
    db = 1

    ;task组件配置
    [task:test_task]
    name = test_task
    broker = amqp://guest:guest@localhost:5672//
    backend = redis://localhost/0
    task_class = some_tasks.add.Add
    queue = test_task_queue
    exchange = test_task_exchange
    routing_key = test_task_routing_key

.. code-block:: python

    """handler（handler.test）"""

    from fastweb import Request
    from fastweb.web import Api, Page
    from fastweb.web import coroutine, run_on_executor

    class Test(Api):

        @coroutine
        @checkArgument(name=str, sex=int)
        def get(self):

            # 加载handler级别线程池
            self.load_executor(5)
            # handler级别线程池示例
            r = yield self.test_executor()

            # mysql使用示例
            ret = yield self.test_mysql.query('select * from table limit 20;')
            print self.test_mysql.fetch()

            # RPC使用示例
            yield self.hello_service.sayHello()

            # Redis使用示例
            yield self.test_redis.call('set', 'name', 'jackson')

            # Http请求示例
            request = Request(method='GET', url='http://www.baidu.com')
            ret = yield self.http_request(request)

            # 任务调用示例
            yield self.test_task.call_async(args=(101, 2))
            x = yield self.test_task.call(args=(101, 2))

            # response
            self.end('SUC', log=False, **{'name':0})

        # 在handler级别线程池中运行
        @run_on_executor
        def test_executor(self):
            time.sleep(10)
            return 1000

    """服务加载组件和启动"""

    from fastweb.web import start_web_server
    from fastweb.loader import app
    from fastweb.pattern import  SyncPattern, AsynPattern

    if __name__ == '__main__':

        options.parse_command_line()
        app.load_recorder('app.log', system_level='DEBUG')
        app.load_configuration(backend='ini', path='component.ini')
        app.load_errcode()
        app.load_component(pattern=AsynPattern, backend='ini', path=options.config)
        app.load_component(pattern=AsynPattern, backend='ini', path='task.ini')

        from handler.test import Test

        handlers = [(r'/test', Test)]

        start_web_server(6666, handlers, debug=True, xheaders=False)


Task层示例
---------

.. code-block:: ini

    ;task配置文件(task.ini)

    ;task组件配置
    [task:test_task]
    name = test_task
    broker = amqp://guest:guest@localhost:5672//
    backend = redis://localhost/0
    task_class = some_tasks.add.Add
    queue = test_task_queue
    exchange = test_task_exchange
    routing_key = test_task_routing_key

.. code-block:: python

    class Add(object):
        """任务"""

        def run(self, x, y):
            return x+y

    if __name__ == '__main__':
        app.load_recorder('task.log', system_level='DEBUG')
        app.load_component(pattern=AsynPattern, backend='ini', path='task.ini')
        start_task_worker()

Service层示例
------------

请参考examples中示例。
        
安装
----

``python setup install``

``pip install fastweb``

适用场景
-------

Fastweb是一个快速构建web应用的框架，与Python的哲学相同，都是期望能够让使用者更快速的开发出满足需求的后端代码。
高速迭代，快速试错，这是使用Fastweb最大的效益！

抉择
----
关于为什么选择 ``Tornado`` ``Celery`` ``Thrift`` 作为Fastweb的工具集合中的重要成员。
