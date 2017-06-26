# coding:utf8


from fastweb import app


class TestLoader(object):

    def test_load_recorder(self):
        app.load_recorder()
        app.load_recorder('log/app.log')
        app.load_recorder('log/app.log', system_log_path='log/sys.log')
        app.load_recorder('log/app.log', system_log_path='log/sys.log')
        app.load_recorder('log/app.log', system_log_path='log/sys.log', application_level='INFO')
        app.load_recorder('log/app.log', system_log_path='log/sys.log', system_level='INFO')

    def test_load_configuration(self):
        app.load_configuration(backend='ini', path='config/config.ini')
        assert app.configs['default_config']['name'] == 'xxxxx'

    def test_load_component(self):
        app.load_component(layout='web', backend='ini', path='config/service.ini')

    def test_load_errcode(self):
        app.load_errcode()

