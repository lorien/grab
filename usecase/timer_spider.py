import setup_script
from grab.spider import Spider, Task
import time
import sys
import logging

class FooSpider(Spider):
    def task_generator(self):
        yield Task('page', 'http://dumpz.org/100/')
        yield Task('page', 'http://dumpz.org/101/', disable_cache=True)

    def task_page(self, grab, task):
        print task.url
        time.sleep(0.2)


logging.basicConfig(level=logging.DEBUG)
skip_generator = 'skip' in ''.join(sys.argv)
bot = FooSpider(skip_generator=skip_generator, thread_number=5)
bot.setup_queue(backend='mongo', database='test', queue_name='skip_test')
bot.setup_cache(backend='mongo', database='test')
bot.run()
print bot.render_stats()
