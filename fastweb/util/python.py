# coding:utf8

"""python特性"""

import os
import six
import json
import hashlib
from importlib import import_module
from thrift.TTornado import TTransportException

import fastweb
from fastweb.accesspoint import coroutine, Return


head = lambda o, h: '{head}{ori}'.format(head=h, ori=o)


def write_file(filepath, content, pattern='a+'):
    with open(filepath, pattern) as f:
        f.write(content)


def filepath2pythonpath(filepath):
    if filepath.startswith('./'):
        filepath = filepath.lstrip('./')

    if filepath.endswith('/'):
        filepath = filepath.rstrip('/')

    pythonpath = filepath.replace('/', '.')
    return pythonpath


def format(st, whole=0):
    if whole:
        return '\n'.join([head(e, whole * ' ') for e in st.split('\n')])
    else:
        return st


def dumps(obj, indent, whole=0):
    if whole:
        return '\n'.join([head(e, whole * ' ') for e in json.dumps(obj, indent=indent).split('\n')])
    else:
        return json.dumps(obj, indent=indent)


def to_iter(e):
    """转换可迭代形式"""

    if isinstance(e, (six.string_types, six.string_types, six.class_types, six.text_type,
                      six.binary_type, six.class_types, six.integer_types, float)):
        return e,
    elif isinstance(e, list):
        return e
    else:
        return e


def to_plain(i):
    """转换不可迭代形式"""

    if isinstance(i, dict):
        plain = ''
        for key, value in i:
            plain += "{key}:{value}".format(key=key, value=value)
        return plain
    elif isinstance(i, (list, set)):
        return ','.join(i)
    else:
        return i


def mixin(cls, mixcls, resume=False):
    """动态继承"""

    mixcls = to_iter(mixcls)

    if resume:
        cls.__bases__ = mixcls
    else:
        for mcls in mixcls:
            cls.__bases__ += (mcls,)


class ExceptionProcessor(object):
    """异常处理器"""

    def __init__(self, exception, processor):
        self.exception = exception
        self.processor = processor


class AsynProxyCall(object):
    """异步调用代理,用来解决__getattr__无法传递多个参数的问题"""

    def __init__(self, proxy, method, throw_exception=None, exception_processor=None):
        self.proxy = proxy
        self._method = method
        self._throw_exception = throw_exception
        self._exception_processor = exception_processor
        self._arg = None
        self._kwargs = None

    @coroutine
    def __call__(self, *arg, **kwargs):
        self._arg = arg
        self._kwargs = kwargs
        self.proxy.recorder('INFO', 'call {proxy} <{method}> start')
        try:
            with fastweb.util.tool.timing('ms', 8) as t:
                ret = yield getattr(self.proxy._other, self._method)(*arg, **kwargs)
            self.proxy.recorder('INFO', 'call {proxy} <{method}> successful\n{ret} <{time}>'.format(proxy=self.proxy,
                                                                                                    method=self._method,
                                                                                                    ret=ret,
                                                                                                    time=t))
            raise Return(ret)
        except TTransportException as e:
            self.proxy.recorder('ERROR',
                                'call {proxy} <{method}> error {e} ({msg})\nreconnect'.format(proxy=self.proxy,
                                                                                              method=self._method,
                                                                                              e=type(e), msg=e))
            yield self._exception_processor.processor()
            self(*self._arg, **self._kwargs)
        else:
            raise self._throw_exception


def load_module(path):
    return import_module(path)


def load_object(path):
    """Load an object given its absolute object path, and return it.

    object can be a class, function, variable or an instance.
    path ie: 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware'
    """
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError("Error loading object '%s': not a full path" % path)

    module, name = path[:dot], path[dot + 1:]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError("Module '%s' doesn't define any object named '%s'" % (module, name))

    return obj


def merge():
    """类合并"""
    pass


def enum(**enums):
    return type('Enum', (), enums)


def isset(v):
    try:
        type(eval(v))
    except:
        return False
    else:
        return True


def md5(s):
    md = hashlib.md5()
    md.update(s)
    return md.hexdigest()





