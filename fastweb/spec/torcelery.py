# coding:utf8

"""tornado调用celery模块"""

from fastweb.accesspoint import states, IOLoop, TracebackFuture


def async(task, *args, **kwargs):
    """celery异步任务

    异步给celery发送命令时，任务的状态为PENDING则视为成功，将任务的taskid返回"""

    future = TracebackFuture()
    callback = kwargs.pop("callback", None)
    if callback:
        IOLoop.instance().add_future(future, lambda f: callback(f.result()))
    result = task.apply_async(*args, **kwargs)
    result.start = IOLoop.instance().time()
    IOLoop.instance().add_callback(_on_async_result, result, future)
    return future


def sync(task, timeout, *args, **kwargs):
    """celery同步任务

    同步给celery发送命令时，任务状态为READY则视为成功，将任务执行的结果返回

    :parameter:
      - `timeout`: 超时时间
    """

    future = TracebackFuture()
    callback = kwargs.pop("callback", None)
    if callback:
        IOLoop.instance().add_future(future, lambda f: callback(f.result()))
    result = task.apply_async(*args, **kwargs)
    IOLoop.instance().add_callback(_on_sync_result, result, future, IOLoop.instance().time(), timeout)
    return future


def _on_async_result(result, future):
    if result.state == states.PENDING:
        future.set_result(result.task_id)
    else:
        IOLoop.instance().add_callback(_on_async_result, result, future)


def _on_sync_result(result, future, start_time, timeout):
    if IOLoop.instance().time()-start_time < timeout:
        if result.successful():
            future.set_result(result.result)
        else:
            IOLoop.instance().add_callback(_on_sync_result, result, future, start_time, timeout)
    else:
        future.set_result(None)
