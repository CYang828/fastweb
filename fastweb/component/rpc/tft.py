# coding:utf8

import os
import six

from thrift import TTornado
from thrift.protocol import TCompactProtocol
from thrift.transport import TTransport, TSocket
from fastweb.accesspoint import coroutine, Return

from fastweb.util.log import recorder
from fastweb.component import Component
from fastweb.exception import RpcError, ConfigurationError
from fastweb.util.python import AsynProxyCall, ExceptionProcessor, load_module


"""
关于Thrift

TftRpc是Thrift客户端的实现，fastweb.service.Service是Thrift服务端的实现

关于Transport:
    Thrift官方实现了多种Transport，目前我们选用的TFrameTransport，主要是为了兼容异步的连接，Thrift的异步链接必须使用TFrameTransport
    
关于Protocal:
    Thrift官方实现了多种Protocal，目前选择的是TCompactProtocol，一种压缩的高性能二进制编码，这种传输方式类似于ProtocolBuffer，性能会
    比TBinaryProtocol高
"""


class TftRpc(Component):

    eattr = {'host': str, 'port': int, 'thrift_module': str}

    def __init__(self, setting):
        super(TftRpc, self).__init__(setting)

        self._client = None
        self._transport = None
        self.other = None

        # 将用户启动的路径加入sys.path，用户普遍理解路径都是从当前目录进行理解
        import sys
        sys.path.append(os.getcwd())
        del sys

    def connect(self):
        raise NotImplementedError

    def reconnect(self):
        raise NotImplementedError

    def ping(self):
        pass

    def _recorder(self, level, msg):
        return self.owner.recorder(level, msg) if self.owner else recorder(level, msg)


class SyncTftRpc(TftRpc):
    """Thrift Rpc同步组件"""

    def __str__(self):
        return '<SyncThriftRpc {name} {host} {port} {module}>'.format(
            host=self.host,
            port=self.port,
            module=self.thrift_module,
            name=self.name)

    def connect(self):
        if isinstance(self.thrift_module, six.string_types):
            module = load_module(self.thrift_module)
        else:
            self.recorder('ERROR', '{obj} module [{module}] load error'.format(obj=self,
                                                                               module=self.thrift_module))
            raise ConfigurationError

        try:
            self.recorder('INFO', '{obj} connect start'.format(obj=self))
            self._transport = TSocket.TSocket(self.host, self.port)
            self._transport = TTransport.TFramedTransport(self._transport)
            protocol = TCompactProtocol.TCompactProtocol(self._transport)
            self._client = getattr(module, 'Client')(protocol)
            self._transport.open()
            self.recorder('INFO', '{obj} connect successful'.format(obj=self))
        except TTransport.TTransportException as e:
            self.recorder('ERROR', '{obj} connect error ({e})'.format(obj=self, e=e)) if self.recorder else recorder('ERROR', '{obj} connect error ({e})'.format(obj=self, e=ex))
            raise RpcError

        return self

    def reconnect(self):
        pass

    def __getattr__(self, name):
        self._client._seqid = int(self.owner.requestid) if self.owner else 0
        if hasattr(self._client, name):
            self._recorder('INFO', 'call {obj} {name} start'.format(obj=self, name=name))
            r = getattr(self._client, name)
            self._recorder('INFO', 'call {obj} {name} success'.format(obj=self, name=name))
            return r
        else:
            raise AttributeError

    def close(self):
        self._transport.close()


class AsynTftRpc(TftRpc):
    """Thrift Rpc异步组件"""

    def __str__(self):
        return '<AsynTftRpc {host} {port} {module} {name}>'.format(
            host=self.host,
            port=self.port,
            module=self.thrift_module,
            name=self.name)

    @coroutine
    def connect(self):
        """建立连接"""

        if isinstance(self.thrift_module, six.string_types):
            module = load_module(self.thrift_module)

        self.recorder('INFO', '{obj} connect start'.format(obj=self))
        self._transport = TTornado.TTornadoStreamTransport(self.host, self.port)
        yield self._connect()
        self.recorder('INFO', '{obj} connect successful'.format(obj=self))
        protocol = TCompactProtocol.TCompactProtocolFactory()
        self._client = getattr(module, 'Client')(self._transport, protocol)
        self.other = self._client
        raise Return(self)

    @coroutine
    def _connect(self):
        try:
            yield self._transport.open()
        except TTransport.TTransportException as e:
            self.recorder('ERROR', '{obj} connect error ({e})'.format(obj=self, e=e)) if self.recorder else recorder('ERROR', '{obj} connect error ({e})'.format(obj=self, e=ex))
            raise RpcError

    def reconnect(self):
        pass

    def __getattr__(self, name):
        """获取远程调用方法"""
        # self._client._seqid = int(self.owner.requestid) if self.owner else 0
        exception_processor = ExceptionProcessor(AttributeError, self._connect)

        if hasattr(self._client, name):
            self._recorder('INFO', 'call {obj} {name} start'.format(obj=self, name=name))
            r = AsynProxyCall(self, name, throw_exception=RpcError, exception_processor=exception_processor)
            self._recorder('INFO', 'call {obj} {name} success'.format(obj=self, name=name))
            return r
        else:
            raise AttributeError

    def close(self):
        """关闭连接"""
        self._transport.close()
