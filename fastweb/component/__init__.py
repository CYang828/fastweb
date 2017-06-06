# coding:utf8


from fastweb.util.log import recorder
from fastweb.exception import ConfigurationError


# 不可用状态,需要进行准备工作才能使用
UNUSED = 1
# 空闲可用状态
IDLE = 2
# 忙碌不可用状态
USED = 3
# 错误不可用状态
ERROR = 4


class Component(object):
    """组件基类

    组件状态流转:组件实例化后的初始状态为UNUSED,准备工作完成后状态为IDLE，被Manager交出将使用权后状态为USED，收回使用权后状态为IDLE
    无法成为IDLE则状态为ERROR状态

    :parameter:
      - `eattr`:组件必须传递参数以及传递参数类型,如果传递类型与标示类型不同,会尝试进行转换,转换失败抛出ConfigurationError
      - `oattr`:组件可选传递参数以及传递参数类型,如果传递类型与标示类型不同,会尝试进行转换,转换失败抛出ConfigurationError
      - `errprocess`:组件自救方式
    """

    eattr = {}
    oattr = {}
    errprocess = {}

    def __init__(self, setting):
        """构建组件,预检查组件

        :parameter:
          - `setting`:构造组件参数
        """

        self.name = None
        # 存储原始的参数
        self._setting = setting
        # 存储转换后的参数
        self.setting = {}
        self.recorder = recorder
        self.status = UNUSED
        self.exceptions = []

        self._check_attrs()

    def set_name(self, name):
        """设置组件名称

        :parameter:
          - `name`:组件名称
        """

        self.name = name
        return self

    def set_unused(self):
        """设置为不可用状态"""

        self.status = UNUSED

    def set_idle(self):
        """设置为空闲可用状态"""

        self.status = IDLE
        self.recorder = recorder

    def set_used(self, logfunc):
        """设置为忙碌可用状态

        :parameter:
          - `logfunc`:日志记录函数
        """

        self.status = USED
        self.recorder = logfunc

    def set_error(self, ex):
        """设置为错误状态,等待回收"""

        self.status = ERROR
        self.exceptions.append(ex)

    def _check_attrs(self):
        """检查组件属性是否合法"""

        def _convert_attrs(att, t, va):
            """转换参数类型"""

            try:
                va = t(va)
                self.setting[att] = va
            except (ValueError, TypeError) as e:
                recorder('ERROR', "<{attr}> can't convert to {tp} ({e})".format(attr=att, tp=t, name=self.name, e=e))
                raise ConfigurationError

        def _add_attr(att, va):
            """增加成员属性"""

            if hasattr(self, att):
                if va:
                    setattr(self, att, va)
            else:
                setattr(self, att, va)

        for attr, tp in self.eattr.iteritems():
            v = self._setting.get(attr)
            _add_attr(attr, v)
            if v:
                _convert_attrs(attr, tp, v)
            else:
                recorder('ERROR', '<{attr}> is essential attribute of <{obj}>'.format(attr=attr, obj=self.__class__))
                raise ConfigurationError

        for attr, tp in self.oattr.iteritems():
            v = self._setting.get(attr)
            _add_attr(attr, v)
            if v:
                _convert_attrs(attr, tp, v)

    def selfrescue(self):
        """自救"""
        pass
