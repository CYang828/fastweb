# coding:utf8


from fastweb.loader import app, SyncPattern
from fastweb.service import start_service_server


if __name__ == '__main__':
    app.load_recorder('service.log', system_log_path='sys.log', system_level='DEBUG')
    app.load_component(pattern=SyncPattern, backend='ini', path='service.ini')
    start_service_server()