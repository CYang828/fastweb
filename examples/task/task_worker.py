# coding:utf8

from fastweb.loader import app
from fastweb.pattern import AsynPattern
from fastweb.task import start_task_worker


if __name__ == '__main__':
    app.load_recorder('task.log', system_level='DEBUG')
    app.load_component(pattern=AsynPattern, backend='ini', path='task.ini')
    start_task_worker()
