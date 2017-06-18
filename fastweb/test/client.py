# coding:utf8
import logging
logging.basicConfig(level=logging.INFO)

import sys
import glob
sys.path.append('gen-py.tornado')

from HelloService import HelloService
from HelloService.ttypes import *

from thrift import TTornado
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.protocol import TMultiplexedProtocol

from tornado import gen
from tornado import ioloop


@gen.coroutine
def communicate():
    # create client
    transport = TTornado.TTornadoStreamTransport('localhost', 9999)
    # open the transport, bail on error
    try:
        yield transport.open()
        print('Transport is opened')
    except TTransport.TTransportException as ex:
        logging.error(ex)
        raise gen.Return()

    protocol = TBinaryProtocol.TBinaryProtocolFactory()
    #pfactory = TMultiplexedProtocol.TMultiplexedProtocol(protocol, 'hello')
    client = HelloService.Client(transport, protocol)

    # ping
    yield client.sayHello()
    print("ping()")

    client._transport.close()
    raise gen.Return()


def main():
    # create an ioloop, do the above, then stop
    import time
    start = time.time()
    for _ in xrange(10000):
        ioloop.IOLoop.current().run_sync(communicate)
    end = time.time()
    print end - start
if __name__ == "__main__":
    main()
