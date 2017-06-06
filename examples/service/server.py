# coding:utf8


from fastweb.service import MicroService
from handlers.hello import HelloServiceHandler


service = MicroService('service_demo', thrift_module='gen-py.HelloService.HelloService', handler=HelloServiceHandler)
service.start(port=8888)