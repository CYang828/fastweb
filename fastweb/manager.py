# coding:utf8

"""组件管理模块"""

import json
from collections import defaultdict

import fastweb.loader
from fastweb.util.log import recorder
from accesspoint import coroutine
from fastweb.exception import ManagerError
from fastweb.pool import ConnectionPool, SyncConnectionPool, AsynConnectionPool


class Manager(object):
    """管理器

    fastweb.setting.default_component.COMPONENTS
    fastweb.setting.default_connection_component.SYNC_CONN_COMPONENTS
    fastweb.setting.default_connection_component.ASYN_CONN_COMPONENTS
    存储组件名称及相应的组件类

    _pools存储所有的组件
    有多种不同的组件，可以复用的组件，在组件管理池中只有一个；不可以复用的组件，组件管理池中需要创建多个，并且存在组件状态
    在取出时判断取出的方式
    """

    # 组件池 _pools: {component_name: component_pool}
    # 被分类的组件池 _classified_pools: {cpre: [obj, obj, ..]}
    _pools = {}
    _classified_pools = defaultdict(list)

    @staticmethod
    def setup(configer):
        """安装组件"""

        recorder('DEBUG', 'default component manager setup start')
        from fastweb.setting.default_component import COMPONENTS

        if configer:
            for (cpre, cls) in COMPONENTS:
                components = configer.get_components(cpre)

                for name, value in components.items():
                    config = configer.configs[name]
                    com = cls(config)
                    Manager._pools[value['object']] = com
                    Manager._classified_pools[cpre].append(com)

        recorder('DEBUG', 'manager setup successful\n{pool}'.format(pool=Manager._pools))

    @staticmethod
    def get_classified_components(cpre):
        """获取被分类的组件"""

        return Manager._classified_pools.get(cpre, [])

    @staticmethod
    def get_component(name, obj):
        """通过manager获取组件

        ManagerError:可能是配置文件错误或者程序错误,应该尽快进行处理,不应该再向下继续运行

        :parameter:
          - `name`:组件名称"""

        pool = Manager._pools.get(name)

        if pool:
            if isinstance(pool, ConnectionPool):
                component = pool.get_connection()
                component.set_used(obj.recorder)
            else:
                component = pool
            return component
        else:
            recorder('CRITICAL',
                     'get component ({name}) error,,please check configuration\n{conf}'.format(conf=json.dumps(fastweb.loader.app.configs), name=name))
            raise ManagerError

    @staticmethod
    def return_component(name, component):
        """归还组件

        :parameter:
          - `name`:组件名称
          - `component`:组件
        """

        pool = Manager._pools.get(name)

        if pool:
            if isinstance(pool, ConnectionPool):
                pool.return_connection(component)
                component.set_idle()
        else:
            recorder('CRITICAL',
                     'please check configuration\n{conf}\n{name}'.format(conf=json.dumps(fastweb.loader.app.configs),
                                                                         name=name))
            raise ManagerError


class SyncConnManager(Manager):
    @staticmethod
    def setup(configer):
        """同步安装组件

         初始化组件时,尽快的抛出准确的错误信息
         """

        recorder('DEBUG', 'synchronize connection component manager setup start')
        from fastweb.setting.default_connection_component import SYNC_CONN_COMPONENTS

        if configer:
            for (cpre, cls, default_size) in SYNC_CONN_COMPONENTS:
                components = configer.get_components(cpre)

                for name, value in components.items():
                    config = configer.configs[name]
                    size = config.get('size', default_size)
                    awake = config.get('awake')
                    maxconnections = config.get('maxconnections')
                    pool = SyncConnectionPool(cls, config, size, name, awake=awake, maxconnections=maxconnections)
                    pool.create()
                    Manager._pools[value['object']] = pool

        recorder('DEBUG', 'synchronize manager setup successful')


class AsynConnManager(Manager):
    configer = None

    @staticmethod
    @coroutine
    def setup():
        """异步安装组件

        初始化组件时,尽快的抛出准确的错误信息
        """

        recorder('DEBUG', 'asynchronous connection component manager setup start')
        from fastweb.setting.default_connection_component import ASYN_CONN_COMPONENTS

        if AsynConnManager.configer:
            for (cpre, cls, default_size) in ASYN_CONN_COMPONENTS:
                components = AsynConnManager.configer.get_components(cpre)

                for name, value in components.items():
                    config = AsynConnManager.configer.configs[name]
                    size = config.get('size', default_size)
                    awake = config.get('awake')
                    maxconnections = config.get('maxconnections')
                    pool = AsynConnectionPool(cls, config, size, name, awake=awake, maxconnections=maxconnections)
                    yield pool.create()
                    Manager._pools[value['object']] = pool

        recorder('DEBUG', 'asynchronous manager setup successful')




