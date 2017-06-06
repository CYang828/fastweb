# coding:utf8


from fastweb.task import task, CeleryTask


@task(name='addTask')
def add(x, y):
    print x+y


@task(name='multiTask')
def multi(x, y):
    print x*y


class LoveTask(CeleryTask):

    name = 'loveTask'

    def run(self):
        print 'love'



