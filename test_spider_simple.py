# coding: utf-8
"""
Quick test to check that Spider refactoring
has not breaked things totally.
"""
from grab.spider import Spider, Task
import logging

class TestSpider(Spider):
    def task_generator(self):
        for x in xrange(3):
            yield Task('yandex', url='http://yandex.ru/')

    def task_yandex(self, grab, task):
        assert grab.xpath_text('//title') == u'Яндекс'
        print grab.xpath_text('//title')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    bot = TestSpider(thread_number=4)
    bot.setup_queue(backend='mongo', database='grab_test')
    #bot.setup_queue(backend='memory')
    bot.run()
