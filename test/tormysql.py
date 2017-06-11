# coding:utf8


from fastweb import coroutine, ioloop
import tornado_mysql
from fastweb.util.tool import timing


@coroutine
def test():
    conn = yield tornado_mysql.connect(**{'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1a2s3dqwe'})
    with timing('ms', 10) as ti:
        for _ in xrange(30):
            cur = conn.cursor(tornado_mysql.cursors.DictCursor)
            with timing('ms', 10) as t:
                yield cur.execute('SELECT * FROM mysql.user;')
            print t

    print 'total:'
    print ti

ioloop.IOLoop.current().run_sync(test)
