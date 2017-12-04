# coding:utf8

"""服务层模块"""

import inspect

from .accesspoint import TServer, TSocket, TTransport, TCompactProtocol

from fastweb import app
from fastweb.manager import Manager
from fastweb.util.tool import timing
from fastweb.util.log import recorder
from fastweb.component import Component
from fastweb.util.process import FProcess
from fastweb.components import SyncComponents
from fastweb.util.python import load_module, to_iter, load_object


__all__ = ['start_service_server', 'ABLogic']
DEFAULT_THREADPOOL_SIZE = 1000


class Service(Component):
    """服务类类

    Thrift服务端实现

    关于Thrift

    TftRpc是Thrift客户端的实现，fastweb.service.Service是Thrift服务端的实现

    关于Transport:
        目前我们选用的TFrameTransport，主要是为了兼容异步的连接，Thrift的异步链接必须使用TFrameTransport

    关于Protocal:
        目前选择的是TCompactProtocol，一种压缩的高性能二进制编码，这种传输方式类似于ProtocolBuffer，性能会比TBinaryProtocol高

    关于Server：
        目前选择的是TThreadPoolServer，多线程的模式处理高并发时效率很高，但是会伴随着系统性能的大量开销。
        TNonBlockingServer为非阻塞IO的多线程模式，使用少量线程既可以完成大并发量的请求响应，必须使用TFramedTransport。
        TNonblockingServer能够使用少量线程处理大量并发连接，但是延迟较高；TThreadedServer的延迟较低。
        实际中，TThreadedServer的吞吐量可能会比TNonblockingServer高，但是TThreadedServer的CPU占用要比TNonblockingServer高很多。

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
        self._active = self.setting.get('active', True)
        self.size = self.setting.get('size', DEFAULT_THREADPOOL_SIZE)

        # 合并多个handler为一个,并自动集成ABLogic
        handlers = tuple(load_object(handler) for handler in handlers)

        try:
            self._handlers = type('Handler', handlers + (ABLogic, ), {})
        except TypeError as e:
            self.recorder('CRITICAL', 'handler conflict ({e})'.format(e=e))

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

        def process_proxy(processor):
            for _func_name, _func in list(processor._processMap.items()):
                def anonymous(p, seq, ipo, opo):
                    oproc = getattr(module, 'Processor')(handler=self._handlers())
                    oproc._handler.requestid = seq if len(str(seq)) > 8 else oproc._handler.requestid
                    oproc._handler.recorder('IMPORTANT', '{obj}\nremote call [{name}]'.format(obj=self, name=_func_name))
                    with timing('ms', 8) as t:
                        _func(oproc, seq, ipo, opo)
                    oproc._handler.release()
                    oproc._handler.recorder('IMPORTANT', '{obj}\nremote call [{name}] success -- {t}'.format(obj=self,
                                                                                                             name=_func_name,
                                                                                                             t=t))
                processor._processMap[_func_name] = anonymous

        # 将所有的handlers合并成一个handler
        module = load_module(self._thrift_module)
        processor = getattr(module, 'Processor')(handler=None)
        process_proxy(processor)
        transport = TSocket.TServerSocket(port=self._port)
        tfactory = TTransport.TFramedTransportFactory()
        pfactory = TCompactProtocol.TCompactProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory, daemon=self._daemon)
        server.setNumThreads(self.size)

        try:
            if self._active:
                recorder('INFO', '{svr} start at <{port}> threadpool size <{size}>'.format(svr=self, port=self._port,
                                                                                           size=self.size))
                server.serve()
        except KeyboardInterrupt:
            recorder('INFO', '{svr} stop at <{port}>'.format(svr=self, port=self._port))


class ABLogic(SyncComponents):
    """基础逻辑类"""

    def __init__(self):
        super(ABLogic, self).__init__()


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

    if not app.bRecorder:
        app.load_recorder()

    # 将调用者路径加入到包查找路径中
    import sys
    sys.path.append(inspect.stack()[1][1])
    del sys

    services = Manager.get_classified_components('service')

    if len(services) == 1:
        # 只有一个service时，只启动一个进程
        services[0].start()
    else:
        # 有多个service会启动多进程
        # 多进程模式下不能使用pdb.set_trace的方式调试
        for service in services:
            process = FProcess(name='ServiceProcess', task=service.start)
            process.start()
