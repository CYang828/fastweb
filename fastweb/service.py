# coding:utf8

"""服务层模块"""

import json
import inspect

from accesspoint import TServer, TSocket, TTransport, TBinaryProtocol

from fastweb.util.log import recorder
from fastweb.util.process import FProcess
from fastweb.exception import ServiceError
from fastweb.web import SyncComponents, Components
from fastweb.util.configuration import Configuration
from fastweb.util.python import load_module, to_iter, load_object


DEFAULT_THREADPOOL_SIZE = 1000


class MicroService(object):
    """微服务类

    多个ABLogic组成一个微服务

    :parameter:
      - `name`:微服务名
      - `thrift_module`:thrift生成模块路径
      - `service_handlers`:处理句柄类对象列表
    """

    def __init__(self, name, thrift_module, handlers):
        self.name = name
        self._module = thrift_module
        self._handler = to_iter(handlers)
        # TODO:handler合并应该遵守一些规则
        self._handler = type('Handler', self._handler, {})() if len(self._handler) > 1 else handlers

    def __str__(self):
        return '<MicroService|{name} {module}->{handler}>'.format(name=self.name,
                                                                  module=self._module,
                                                                  handler=self._handler)

    def start(self, port, size, daemon=True):
        """微服务开始

        生成一个微服务

        :parameter:
         - `handler`:AbLogic列表
        """

        # 将所有的handlers合并成一个handler
        port = int(port)
        module = load_module(self._module)
        processor = getattr(module, 'Processor')(self._handler())
        transport = TSocket.TServerSocket(port=port)
        tfactory = TTransport.TFramedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory, daemon=daemon)
        server.setNumThreads(size)
        recorder('INFO', '{svr} start at <{port}> threadpool size <{size}>'.format(svr=self, port=port, size=size))

        try:
            server.serve()
        except KeyboardInterrupt:
            recorder('INFO', '{svr} stop at <{port}>'.format(svr=self, port=port))


class ABLogic(SyncComponents):
    """基础逻辑类"""

    def __init__(self):
        super(ABLogic, self).__init__()


class Table(Components):
    """库表类"""

    def __init__(self):
        super(Table, self).__init__()


def start_server(config_path):
    """强制使用config的方式来配置微服务

    port: 启动端口号,如果为列表则生成多个进程,配置必填项
    thrift_module:  thrift生成的模块类路径,系统可查找或相对启动路径类路径,只能有一个
    service_handlers: 处理具体业务的handler类,可以为列表或单个类
    daemon: 是否以守护进程的形式启动
    active: 是否可用
    size: 线程池大小

    :parameter:
      - `config_path`:配置文件路径
    """

    configuration = Configuration(backend='ini', path=config_path)
    microservices = configuration.get_components('microservice')

    recorder('INFO', 'service configuration\n{conf}'.format(conf=json.dumps(configuration.configs, indent=4)))

    for name, value in microservices.items():
        config = configuration.configs[name]
        name = value['object']

        port = config.get('port')
        if not port or not isinstance(port, (float, list)):
            recorder('CRITICAL', 'please specify port {conf}'.format(conf=config))
            raise ServiceError

        ports = to_iter(port)

        # 将调用者路径加入到包查找路径中
        import sys
        sys.path.append(inspect.stack()[1][1])
        del sys

        # 每个微服务只能在thrift中指定一个service,对应只有一个thrift模块
        thrift_module = config.get('thrift_module')
        if not thrift_module or not isinstance(thrift_module, str):
            recorder('CRITICAL', 'please specify thrift_module {conf}'.format(conf=config))
            raise ServiceError

        handlers = config.get('handlers')
        if isinstance(handlers, list):
            handlers = [load_object(handler) for handler in handlers]
        elif isinstance(handlers, str):
            handlers = load_object(handlers)
        if not handlers or isinstance(handlers, (str, list)):
            recorder('CRITICAL', 'please specify handlers {conf}'.format(conf=config))
            raise ServiceError

        # 默认为守护进程
        daemon = config.get('daemon', True)
        # 默认微服务不活跃
        active = config.get('active', False)
        size = config.get('size', DEFAULT_THREADPOOL_SIZE)

        if active:
            for port in ports:
                microservice = MicroService(name, thrift_module=thrift_module, handlers=handlers)
                process = FProcess(name='microservice', task=microservice.start, port=port, size=size, daemon=daemon)
                process.start()
