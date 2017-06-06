# coding:utf8

"""任务层模块"""

from fastweb.web import SyncComponents
from fastweb.util.python import load_module
from fastweb.accesspoint import Task, platforms, Celery, Ignore, task


class CeleryTask(Task, SyncComponents):
    """Celery Task基类

    类成员变量name为任务名称
    run方法为接受参数并运行的函数
    on_success方法为成功回调函数
    on_failure方法为异常回调函数
    on_retry方法为重试回调函数
    """

    def __init__(self, setting):
        super(CeleryTask, self).__init__()

    # TODO:任务类，定时任务类，异步任务类，同步任务类


def celery_from_object(obj_path=None, force_root=False):
    """通过模块构建celery对象

    :parameter:
      - `obj_path`: celery配置文件模块路径
      - `force_root`: root用户可否启动"""

    if obj_path:
        obj = load_module(obj_path)
    platforms.C_FORCE_ROOT = force_root
    celery = Celery()
    obj_path and celery.config_from_object(obj)
    return celery
