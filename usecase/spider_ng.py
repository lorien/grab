import setup_script
from grab.spider import Spider
from grab.spider.ng import (BaseWorkerSpider, BaseManagerSpider,
                            BaseDownloaderSpider,
                            BaseParserSpider,
                            build_generator_spider,
                            build_parser_spider,
                            Task, Data, create_process)
import logging
import pymongo
from multiprocessing import Manager, Queue, Event, active_children
from Queue import Empty
import time
from urlparse import urlsplit

logger = logging.getLogger('usecase.spider_ng')

class SimpleParserSpider(Spider):
    initial_urls = ['http://dumpz.org']

    def task_generator(self):
        yield Task('page', url='http://flask.pocoo.org/')
        time.sleep(1)
        yield Task('page', url='http://ya.ru/')

    def task_initial(self, grab, task):
        for res in self.task_page(grab, task):
            yield res

    def task_page(self, grab, task):
        host = urlsplit(task.url).netloc
        if not task.get('secondary'):
            title = grab.doc.select('//title').text()
            yield Task('page', url='http://%s/robots.txt' % host, secondary=True)
            open('var/%s.txt' % host, 'w').write(grab.response.body)


def start_spider(spider_cls):
    try:
        result_queue = Queue()
        response_queue = Queue()
        shutdown_event = Event()
        generator_done_event = Event()
        taskq = Queue()

        args = (taskq, result_queue, response_queue, shutdown_event, generator_done_event)
        kwargs = dict(verbose_logging=True)

        generator_wating_shutdown_event = Event()
        generator_cls = build_generator_spider(spider_cls)
        generator = create_process(generator_cls, generator_wating_shutdown_event,
                                   *args, **kwargs)
        generator.start()

        downloader_wating_shutdown_event = Event()
        downloader = create_process(BaseDownloaderSpider, downloader_wating_shutdown_event,
                                    *args, **kwargs)
        downloader.start()

        parser_wating_shutdown_event = Event()
        parser_cls = build_parser_spider(spider_cls)
        parser = create_process(parser_cls, parser_wating_shutdown_event,
                                *args, **kwargs)
        parser.start()

        while True:
            time.sleep(2)
            print 'task size', taskq.qsize()
            print 'response size', response_queue.qsize()
            if (downloader_wating_shutdown_event.is_set() and
                parser_wating_shutdown_event.is_set()):
                shutdown_event.set()
                break

        time.sleep(1)

        print 'done'
    finally:
        for child in active_children():
            logging.debug('Killing child process (pid=%d)' % child.pid)
            child.terminate()


def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')
    logger = logging.getLogger('grab.verbose.spider.ng.downloader')
    logger.propagate = False
    logger.setLevel(logging.FATAL)


if __name__ == '__main__':
    setup_logging()
    start_spider(SimpleParserSpider)
