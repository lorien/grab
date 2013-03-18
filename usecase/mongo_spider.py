import setup_script
from grab.spider import Spider, Task
import time
import sys
import logging

class FooSpider(Spider):
    def task_generator(self):
        for x in xrange(10):
            yield Task('page', 'http://dumpz.org/%d/' % x)

    def task_page(self, grab, task):
        print task.url
        time.sleep(1)

logging.basicConfig(level=logging.DEBUG)
skip_generator = 'skip' in ''.join(sys.argv)
bot = FooSpider(skip_generator=skip_generator, thread_number=1)
bot.setup_queue(backend='mongo', database='test', queue_name='skip_test')
bot.run()
