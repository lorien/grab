# coding: utf-8

from random import shuffle
from unittest import TestCase, main

from grab.spider import Spider, Task

from util import (FakeServerThread, RESPONSE, SLEEP, BASE_URL,
                  reset_env)


# TEMPORARY DISABLED DUE TO ERROR
#class TestSpider(TestCase):
    #def setUp(self):
        #FakeServerThread().start()
        #reset_env()

    #def test_spider(self):
        #TASK_COUNT = 10

        #class SimpleSpider(Spider):
            #def prepare(self):
                #self.tasks = range(TASK_COUNT)
                #shuffle(self.tasks)
                #self.tasks_order = []

            #def task_generator(self):
                #for index in self.tasks:
                    #yield Task(
                        #name='foo',
                        #url=BASE_URL,
                        #priority=index,
                        #index=index,
                        #first=True
                    #)

            #def task_foo(self, grab, task):
                #self.tasks_order.append(task.index)

                #if task.get('first', False):
                    #yield Task(
                        #name=task.name,
                        #priority=TASK_COUNT + task.priority,
                        ##url=BASE_URL,
                        #grab=grab,
                        #index=task.index
                    #)

        #RESPONSE['get'] = 'Hello spider!'
        #SLEEP['get'] = 0

        #sp = SimpleSpider(thread_number=5)
        #sp.setup_queue(backend='mongo', database='queue_test')
        #sp.run()

        #self.assertEqual(range(TASK_COUNT) * 2, sp.tasks_order)


if __name__ == '__main__':
    main()
