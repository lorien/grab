from multiprocessing import Process
import logging
from multiprocessing import Queue, Event, active_children
import time
try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit
import os

from grab.spider import Spider, Task
from grab.spider.queue_backend.redis import QueueBackend

from grab.util.py3k_support import *

logger = logging.getLogger('ng')


class SimpleParserSpider(Spider):
    initial_urls = ['http://dumpz.org']

    def task_generator(self):
        yield Task('page', url='http://flask.pocoo.org/')
        time.sleep(1)
        yield Task('page', url='http://ya.ru/')
        yield Task('page', url='http://rambler.ru/')
        yield Task('page', url='http://mail.ru/')

    def task_initial(self, grab, task):
        for res in self.task_page(grab, task):
            yield res

    def task_page(self, grab, task):
        print(task.url)
        title = grab.doc.select('//title').text(default=None)
        print('TITLE:', title, 'PID:', os.getpid())
        host = urlsplit(task.url).netloc
        if not task.get('secondary'):
            yield Task('page', url='http://%s/robots.txt' % host, secondary=True)
            open('var/%s.txt' % host, 'w').write(grab.response.body)


def start_spider(spider_cls):
    try:
        result_queue = Queue()
        network_response_queue = Queue()
        shutdown_event = Event()
        generator_done_event = Event()
        taskq = QueueBackend('ng')

        #from grab.spider.base import logger_verbose
        #logger_verbose.setLevel(logging.DEBUG)

        kwargs = {
            'taskq': taskq,
            'result_queue': result_queue,
            'network_response_queue': network_response_queue,
            'shutdown_event': shutdown_event,
            'generator_done_event': generator_done_event,
            'ng': True,
        }

        # Generator: OK
        generator_waiting_shutdown_event = Event()
        bot = spider_cls(waiting_shutdown_event=generator_waiting_shutdown_event, **kwargs)
        generator = Process(target=bot.run_generator)
        generator.start()

        # Downloader: OK
        downloader_waiting_shutdown_event = Event()
        bot = spider_cls(waiting_shutdown_event=downloader_waiting_shutdown_event,
                         **kwargs)
        downloader = Process(target=bot.run)
        downloader.start()

        # Parser: OK
        events = []
        for x in xrange(2):
            parser_waiting_shutdown_event = Event()
            events.append(parser_waiting_shutdown_event)
            bot = spider_cls(waiting_shutdown_event=parser_waiting_shutdown_event,
                             **kwargs)
            parser = Process(target=bot.run_parser)
            parser.start()

        while True:
            time.sleep(2)
            print('task size', taskq.size())
            print('response size', network_response_queue.qsize())
            if (downloader_waiting_shutdown_event.is_set() and
                all(x.is_set() for x in events)):
                shutdown_event.set()
                break

        time.sleep(1)

        print('done')
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
