# coding:utf8


from fastweb.loader import app
from fastweb.service import start_service_server


app.load_recorder('service.log', system_log_path='sys.log', system_level='DEBUG')
if __name__ == '__main__':
    start_service_server('service.ini')