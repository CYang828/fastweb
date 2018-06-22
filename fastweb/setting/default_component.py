# coding:utf8

from fastweb.task import Worker
from fastweb.service import Service
from fastweb.component.task import AsynTask, SyncTask


# 不区分同步异步的组件
COMPONENTS = [('worker', Worker),
              ('service', Service)]
# 同步组件
SYNC_COMPONENTS = [('task', SyncTask)]
# 异步组件
ASYN_COMPONENTS = [('task', AsynTask)]


