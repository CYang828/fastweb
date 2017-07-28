# coding:utf8


from fastweb import app


class TestLoader(object):

    def test_load_recorder(self):
        app.load_recorder()
        app.load_recorder('app.log')
        app.load_recorder('app.log', system_log_path='sys.log')
        app.load_recorder('app.log', system_log_path='sys.log')
        app.load_recorder('app.log', system_log_path='sys.log', application_level='INFO')
        app.load_recorder('app.log', system_log_path='sys.log', system_level='INFO')

    def test_load_configuration(self):
        app.load_configuration(backend='ini', path='fastweb/test/config/config.ini')
        assert app.configs['default_config']['name'] == 'xxxxx'

    def test_load_component(self):
        app.load_component(layout='web', backend='ini', path='fastweb/test/config/component.ini')

    def test_load_errcode(self):
        app.load_errcode()

