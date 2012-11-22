import setup_script
from grab.spider.ng import Spider, Task, Data, Actor
import logging
import pymongo
from multiprocessing import Manager
import time

class SimpleSpider(Spider):
    def task_generator(self):
        yield Task('page', url='http://yandex.ru')

    def task_page(self, grab, task):
        title = grab.xpath_text('//title')
        page = {
            'url': task.url,
            'title': title,
        }
        logging.debug('PAGE SAVED!!!!!!!!!!')
        yield Data('page', page)

    def data_page(self, page):
        self.db.page.save(page)

    def setup_manager(self):
        self.db = pymongo.Connection()['ng']


logging.basicConfig(level=logging.DEBUG)

man = Manager()
result_queue = man.Queue()
manager = Actor(SimpleSpider, 'manager', result_queue,
                spider_kwargs={'verbose_logging': True})
manager.start()

time.sleep(1)
worker = Actor(SimpleSpider, 'worker', result_queue,
               spider_kwargs={'verbose_logging': True})
worker.start()

manager.join()
worker.terminate()
