# coding:utf8

import six
from importlib import import_module

from thrift import TTornado
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol
from fastweb.accesspoint import coroutine, Return

from fastweb.util.log import recorder
from fastweb.component import Component
from fastweb.exception import RpcError, ConfigurationError
from fastweb.util.python import AsynProxyCall, ExceptionProcessor, load_module


class TftRpc(Component):

    eattr = {'host': str, 'port': int, 'thrift_module': str}

    def __init__(self, setting):
        super(TftRpc, self).__init__(setting)

        self.isConnect = False
        self._client = None
        self._module = None
        self._transport = None
        self._other = None

    def connect(self):
        raise NotImplementedError

    def reconnect(self):
        raise NotImplementedError


class SyncTftRpc(Component):
    """Thrift Rpc同步组件"""

    def __init__(self, **kwargs):
        super(SyncTftRpc, self).__init__(**kwargs)

        self.isConnect = False

    def __str__(self):
        return '<SyncThriftRpc {name} {host} {port} {module_path} {module}>'.format(
            host=self.host,
            port=self.port,
            module_path=self.thrift_module_path,
            module=self.thrift_module,
            name=self.name)

    def connect(self):
        if isinstance(self.module, six.string_types):
            module = import_module(self.module)
        else:
            self.recorder('ERROR', '{obj} module [{module}] error'.format(obj=self, module=self.module))
            raise ConfigurationError

        try:
            transport = TSocket.TSocket(host, port)
            self._transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            pfactory = TMultiplexedProtocol.TMultiplexedProtocol(protocol, service_name)
            self._transport.open()
            self.client = getattr(module, 'Client')(pfactory)
        except:
            raise RpcError

    def __getattr__(self, name):
        if hasattr(self.client, name):
            return getattr(self.client, name)

    def close(self):
        self.transport.close()


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
            self._module = load_module(self.thrift_module)

        self.recorder('INFO', '{obj} connect start'.format(obj=self))
        self._transport = TTornado.TTornadoStreamTransport(self.setting['host'], self.setting['port'])
        yield self._connect()
        self.set_idle()
        self.isConnect = True
        self.recorder('INFO', '{obj} connect successful'.format(obj=self))
        protocol = TBinaryProtocol.TBinaryProtocolFactory()
        self._client = getattr(self._module, 'Client')(self._transport, protocol)
        self._other = self._client
        raise Return(self)

    @coroutine
    def _connect(self):
        try:
            yield self._transport.open()
        except TTransport.TTransportException as ex:
            self.recorder('ERROR', '{obj} connect error ({e})'.format(obj=self, e=ex)) if self.recorder else recorder('ERROR', '{obj} connect error ({e})'.format(obj=self, e=ex))
            raise RpcError

    def reconnect(self):
        pass

    def __getattr__(self, name):
        """获取远程调用方法"""

        exception_processor = ExceptionProcessor(AttributeError, self._connect)

        if hasattr(self._client, name):
            return AsynProxyCall(self, name, throw_exception=RpcError, exception_processor=exception_processor)
        else:
            raise AttributeError

    def close(self):
        """关闭连接"""

        if self.transport:
            self.transport.close()
