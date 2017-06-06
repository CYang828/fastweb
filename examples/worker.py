# coding:utf8


from fastweb.task import celery_from_object

# 该种导入方式，所有的装饰器热任务都会被加载，但是任务类不会
# import task.add

from task.add import LoveTask

celery = celery_from_object()
print celery.current_task
print celery.tasks
celery.start()
