#!/usr/bin/python2.7
# *-*coding:utf8*-*
#
# Copyright 2015 Adapter
#

"""Service entrance.

Add handler and load super global variables here.

"""

import os

from fastweb import options
from fastweb.web import start_server
from fastweb.loader import app
from fastweb.pattern import  SyncPattern, AsynPattern

options.define('port',default = 6666,help = 'this is default port',type = int)
options.define('config',default = 'config.ini',help = 'this is default config path',type = str)

if __name__ == '__main__':
    
    options.parse_command_line()
    app.load_recorder('app.log', system_level='DEBUG')
    app.load_configuration(backend='ini', path=options.config)
    app.load_errcode()
    app.load_component(pattern=AsynPattern)

    from handlers.test import Test, ZohoOffice

    handlers = [
                  (r'/test', Test),
                  (r'/zoho', ZohoOffice)
               ]

    # template_path=os.path.join(os.path.dirname(__file__), "templates")
    # static_path=os.path.join(os.path.dirname(__file__), "static")
    # start_server(options.port, service_handlers, template_path=template_path, static_path=static_path, debug=True, xheaders=True)
    start_server(options.port, handlers, debug=True, xheaders=False)
