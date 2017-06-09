# coding:utf8


import re
import collections
import ConfigParser

from fastweb.util.log import recorder
from fastweb.util.python import to_iter
from fastweb.exception import ParameterError


class Configuration(object):
    """配置解析

    TODO:支持多种配置后端,后续改造
    """

    parser = {'ini': '_ini_parser', 'confd': '_confd_parser'}

    def __init__(self, backend, **setting):
        """获取配置信息

        configs:{'section': {setting}}

        :parameter:
          - `backend`:后端类型
          - `setting`:根据后端类型相关的配置项
        """

        self.configs = None
        self.get_configs_from_backend(backend, setting)

    @staticmethod
    def _check_setting(eattr, setting):
        """检查配置

        :parameter:
          - `eattr`:必要配置
          - `setting`:传入参数,参数不足抛出ParameterError
        """

        for attr in eattr:
            v = setting.get(attr)
            if not v:
                recorder('CRITICAL', 'configuration backend setting error! right options {options}'.format(options=eattr))
                raise ParameterError

    def _ini_parser(self, setting):
        """ini配置文件解析

        :parameter:
          - `setting`:传入参数
        """

        eattr = ['path']
        self._check_setting(eattr, setting)
        path = setting.get('path')
        cf = ConfigParser.ConfigParser()
        cf.read(path)
        configs = collections.defaultdict(dict)

        for section in cf.sections():
            options = cf.items(section)
            for key, value in options:
                value = self._type_conversion(value)
                configs[section][key] = value
        return configs

    def _confd_parser(self, setting):
        """confd"""
        pass

    @staticmethod
    def _type_conversion(v):
        """尝试转换配置文件中的value类型"""

        # 数字解析
        if v.isdigit():
            return int(v)

        # 列表解析
        l = v.split(',')
        if len(l) > 1:
            return [i for i in l if i]

        # boolean解析
        lv = v.lower()
        if lv == 'yes':
            return True
        elif lv == 'no':
            return False
        else:
            return v

    def get_configs_from_backend(self, backend, setting):
        """从不同的backend获取相同格式的配置

        :parameter:
          - `backend`:后端类型,后端类型不正确抛出ParameterError
          - `setting`:传入参数
        """

        parser = self.parser.get(backend)
        if parser:
            self.configs = getattr(self, parser)(setting)
        else:
            raise ParameterError

    def get_components(self, components):
        """根据组件名称获取组件配置

        :parameter:
          - `components`:组件名称

        :return:
          {section: {'component': component_name, 'object': component_type}}
        """

        match_components = {}
        components = to_iter(components)

        for component in components:
            component_exp = r'(%s):(\w*)' % component
            exp = re.compile(component_exp)

            for section in self.configs.keys():
                match = exp.match(section)
                if match:
                    match_components[section] = {'component': match.group(1), 'object': match.group(2)}

        return match_components
