# coding:utf8

"""call celery task from a task config

Usage:
    fastcelery <task_name> <configpath> [--args=<arg>]

Options:
    -h --help     Show this screen.
    --args=<arg>  Remote task arguments.
"""

import os

from fastweb import app
from fastweb.manager import Manager
from fastweb.accesspoint import docopt
from fastweb.web import coroutine, ioloop
from fastweb.util.python import guess_type


args = docopt(__doc__)


class CeleryCommand(object):

    @coroutine
    def call_celery_task(self):
        arg = args['--args']
        task_name = args['<task_name>']
        arg = [guess_type(a) for a in arg.split(',')]
        yield Manager.get_component(task_name, self).call(arg)


def call_celery_task():
    cwd = os.getcwd()
    import sys
    sys.path.append(cwd)
    del sys
    configpath = args['<configpath>']
    app.load_recorder('fastcelery.log')
    app.load_component(layout='web', backend='ini', path=configpath)
    celery = CeleryCommand()
    ioloop.IOLoop.current().run_sync(celery.call_celery_task)

