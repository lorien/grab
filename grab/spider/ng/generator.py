import time
import Queue
import logging

from ..task import Task
from ..data import Data
from ..error import SpiderError
from .base import BaseNGSpider

logger = logging.getLogger('grab.spider.ng.generator')

class BaseGeneratorSpider(BaseNGSpider):
    def setup_task_generator(self):
        self.task_generator_object = self.task_generator()
        self.task_generator_enabled = True

        self.log_verbose('Processing initial urls')
        self.load_initial_urls()
        self.process_task_generator()

    def run(self):
        self.run_generator()

    def run_generator(self):
        self.setup_task_generator()

        while True:
            if not self.task_generator_enabled:
                self.generator_done_event.set()
            if self.shutdown_event.is_set():
                logger.info('Got shutdown event')
                break
            time.sleep(1)
            self.process_task_generator()
