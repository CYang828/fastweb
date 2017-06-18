# coding:utf8


"""测试subprocess性能"""

import shlex
import subprocess

from gevent.pool import Pool
import gevent.subprocess

from fastweb.util.tool import timing
from fastweb.util.thread import FThread


def call_subprocess(obj):
    returncode = subprocess.call(shlex.split('ls'))
    print 'returncode: {}'.format(returncode)


def call_subprocess_gevent():
    returncode = gevent.subprocess.call(shlex.split('ls'))
    print returncode


if __name__ == '__main__':

    b = True

    x = 1000

    with timing('s', 8) as t:
        if b:
            for i in range(x):
                FThread("Thread-{}".format(i), call_subprocess, frequency=1).start()
            FThread.stop()
        else:
            pool = Pool(x)
            for i in range(x):
                pool.spawn(call_subprocess_gevent)
            pool.join()

    print 'total cost: {}'.format(t)


