# coding:utf8

"""异常模块"""


class FastwebException(Exception):
    """fastweb框架异常"""
    pass


class ComponentError(FastwebException):
    """组件错误"""
    pass


class HttpError(ComponentError):
    """HTTP访问错误"""
    pass


class SubProcessError(ComponentError):
    """子进程调用错误"""
    pass


class MysqlError(ComponentError):
    """mysql组件错误"""
    pass


class RedisError(ComponentError):
    """redis组件错误"""
    pass


class MongoError(ComponentError):
    """mongo组件错误"""
    pass


class RpcError(ComponentError):
    """rpc组件错误"""
    pass


class ConfigurationError(FastwebException):
    """配置错误"""
    pass


class ConnectionPoolError(FastwebException):
    """连接池错误"""
    pass


class ManagerError(FastwebException):
    """管理器错误"""
    pass


class ParameterError(FastwebException):
    """参数错误"""
    pass


class ServiceError(FastwebException):
    """服务层错误"""
    pass


class TaskError(ComponentError):
    """任务错误"""
    pass


class ThriftParserError(ComponentError):
    """thrift文件解析错误"""
    pass
