# coding:utf8


from fastweb.task import task


@task(name='minusTask')
def add(x, y):
    print x-y