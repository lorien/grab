import setup_script
from grab.spider.ng import (BaseWorkerSpider, BaseManagerSpider,
                            Task, Data, create_process)
import logging
import pymongo
from multiprocessing import Manager
import time

class SimpleSpider(BaseWorkerSpider):
    def task_generator(self):
        yield Task('page', url='http://flask.pocoo.org/', level=0)

    def task_page(self, grab, task):
        title = grab.xpath_text('//title')
        page = {
            '_id': task.url,
            'url': task.url,
            'title': title,
        }
        yield Data('page', page)

        if task.level == 0:
            for elem in grab.xpath('//p[@class="nav"]/a'):
                yield Task('page', page, level=task.level + 1)

    def data_page(self, page):
        logging.debug('Saving data: %s' % page['_id'])
        self.db.page.save(page)

    def prepare(self):
        self.db = pymongo.Connection()['ng']


def main():
    logging.basicConfig(level=logging.DEBUG)

    mp_manager = Manager()
    result_queue = mp_manager.Queue()

    manager = create_process(BaseManagerSpider, result_queue,
                             verbose_logging=True)
    manager.start()

    time.sleep(1)

    worker = create_process(SimpleSpider, result_queue,
                            verbose_logging=True)
    worker.start()

    manager.join()
    print 'MANAAGER HAS STOPED'
    worker.terminate()


if __name__ == '__main__':
    main()
