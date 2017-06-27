# coding:utf8


"""call fastweb component

Usage:
    fast <configpath>

Options:
    -h --help     Show this screen.
    --args=<arg>  Remote task arguments.
"""


import os
import re

from fastweb import app
from fastweb.accesspoint import docopt
from fastweb.util.tool import HistoryConsole
from fastweb.components import SyncComponents
from fastweb.exception import FastwebException
from fastweb.util.log import console_recorder, colored


def main():
    cwd = os.getcwd()
    import sys
    sys.path.append(cwd)
    del sys
    args = docopt(__doc__)
    configpath = args['<configpath>']
    configpath = os.path.join(cwd, configpath)
    app.load_component(layout='service', backend='ini', path=configpath)
    components = SyncComponents()
    console_recorder('DEBUG', "[Fast command]\nyou can call any component like in fastweb")
    argexp = re.compile(r'(.*)\((.*)\)')
    console = HistoryConsole()

    while True:
        c = console.raw_input(colored('>>> ', 'cyan'))

        if c in ('quit', 'quit()', 'exit', 'exit()'):
            break
        else:
            cplit = c.split('.')

            if cplit[0] != 'self':
                console_recorder('ERROR', 'error, please use `self` first!')
                continue

            try:
                if len(cplit) > 1:
                    cname = cplit[1]
                    com = getattr(components, cname)

                if len(cplit) > 2:
                    cfunc = cplit[2]
                    match = argexp.match(cfunc)

                    if match:
                        func = match.group(1)
                        args = match.group(2)
                        if args:
                            args = args.split(',')
                            print(getattr(com, func)(*args))
                        else:
                            print(getattr(com, func)())
                    else:
                        console_recorder('ERROR', 'error! please input function!')
                        continue
            except FastwebException as e:
                console_recorder('ERROR', 'error! {e}'.format(e=e))
                continue




