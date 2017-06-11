Fastweb Web Server
==================

依赖 ``Tornado`` ``Celery`` ``Thrift`` 开发的快速构建web应用的框架。

示例
----

下面是一个例子:

.. code-block:: python

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
            ret = yield self.test_mysql.query('select * from entity_question limit 20;')
            print self.test_mysql.fetch()

            # RPC使用示例
            yield self.hello_service.sayHello()

            # Redis使用示例
            yield self.test_redis.call('set', 'name', 'jackson')

            # Http请求示例
            request = Request(method='GET', url='http://www.baidu.com')
            ret = yield self.http_request(request)

            # response
            self.end('SUC', log=False, **{'name':0})

        # 在handler级别线程池中运行
        @run_on_executor
        def test_executor(self):
            time.sleep(10)
            return 1000
        
安装
----

``python setup install``

``pip install fastweb``

迷思
----

Fastweb是一个快速构建web应用的框架，与Python的哲学相似，都是期望能够让使用者更快速的开发出满足需求的后端代码。
关于为什么选择 ``Tornado`` ``Celery`` ``Thrift`` 作为Fastweb的工具集合中的重要成员，其实是有原因的。

:: 

    Tornado is a Python web framework and asynchronous networking library, originally developed at FriendFeed. By using non-blocking network I/O, Tornado can scale to tens of thousands of open connections, making it ideal for long polling, WebSockets, and other applications that require a long-lived connection to each user.

::

    Celery is an asynchronous task queue/job queue based on distributed message passing.	It is focused on real-time operation, but supports scheduling as well.

::

    The Apache Thrift software framework, for scalable cross-language services development, combines a software stack with a code generation engine to build services that work efficiently and seamlessly between multiple languages.
