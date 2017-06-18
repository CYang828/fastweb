# coding:utf8

"""服务层模块"""

import inspect

from accesspoint import TServer, TSocket, TTransport, TBinaryProtocol

from fastweb.manager import Manager
from fastweb.util.log import recorder
from fastweb.component import Component
from fastweb.util.process import FProcess
from fastweb.components import SyncComponents, Components
from fastweb.util.python import load_module, to_iter, load_object


__all__ = ['start_service_server', 'ABLogic']
DEFAULT_THREADPOOL_SIZE = 1000


class Service(Component):
    """微服务类

    多个ABLogic组成一个微服务

    :parameter:
      - `port`: 启动端口号,如果为列表则生成多个进程,配置必填项
      - `thrift_module`:thrift生成模块路径，系统可查找或相对启动路径类路径,只能有一个
      - `handlers`: 处理具体业务的handler类,可以为列表或单个类
      - `daemon`: 是否以守护进程的形式启动
      - `active`: 是否可用
      - `size`: 线程池大小
    """

    eattr = {'port': int, 'thrift_module': str, 'handlers': str}
    oattr = {'size': int, 'daemon': bool, 'active': bool}

    def __init__(self, setting):
        super(Service, self).__init__(setting)

        # 设置service属性
        self._port = self.setting['port']
        self._thrift_module = self.setting['thrift_module']
        self._handlers = self.setting['handlers']
        handlers = to_iter(self._handlers)
        self._daemon = self.setting.get('daemon', True)
        self._active = self.setting.get('active', False)
        self.size = self.setting.get('size', DEFAULT_THREADPOOL_SIZE)

        # 合并多个handler为一个
        # TODO:handler合并应该遵守一些规则
        if isinstance(self._handlers, (tuple, list)):
            self._handlers = (load_object(handler) for handler in self._handlers)
        elif isinstance(self._handlers, str):
            self._handlers = (load_object(self._handlers))

        try:
            self._handlers = type('Handler', handlers, {})() if len(handlers) > 1 else self._handlers
        except TypeError as e:
            self.recorder('CRITICAL', 'handler conflict (e)'.format(e=e))

    def __str__(self):
        return '<Service|{name} {port} {module}->{handler}>'.format(name=self.name,
                                                                    port=self._port,
                                                                    module=self._thrift_module,
                                                                    handler=self._handlers)

    def start(self):
        """微服务开始

        生成一个微服务

        :parameter:
         - `handler`:AbLogic列表
        """

        # 将所有的handlers合并成一个handler
        module = load_module(self._thrift_module)
        processor = getattr(module, 'Processor')(self._handlers())
        transport = TSocket.TServerSocket(port=self._port)
        tfactory = TTransport.TFramedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory, daemon=self._daemon)
        server.setNumThreads(self.size)
        recorder('INFO', '{svr} start at <{port}> threadpool size <{size}>'.format(svr=self, port=self._port, size=self.size))

        try:
            server.serve()
        except KeyboardInterrupt:
            recorder('INFO', '{svr} stop at <{port}>'.format(svr=self, port=self._port))


class ABLogic(SyncComponents):
    """基础逻辑类"""

    def __init__(self):
        super(ABLogic, self).__init__()
        # 生成requestid
        self.requestid = self.gen_requestid()


def start_service_server():
    """强制使用config的方式来配置微服务

    port: 启动端口号,如果为列表则生成多个进程,配置必填项
    thrift_module:  thrift生成的模块类路径,系统可查找或相对启动路径类路径,只能有一个
    handlers: 处理具体业务的handler类,可以为列表或单个类
    daemon: 是否以守护进程的形式启动
    active: 是否可用
    size: 线程池大小

    :parameter:
      - `config_path`:配置文件路径
    """

    # 将调用者路径加入到包查找路径中
    import sys
    sys.path.append(inspect.stack()[1][1])
    del sys

    services = Manager.get_classified_components('service')

    for service in services:
        process = FProcess(name='ServiceProcess', task=service.start)
        process.start()
