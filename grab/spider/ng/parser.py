import logging
import time
from Queue import Empty

from ..task import Task
from ..data import Data
from ..error import SpiderError
from .base import BaseNGSpider

from ..transport.multicurl import MulticurlTransport

logger = logging.getLogger('grab.spider.ng.parser')
logger_verbose = logging.getLogger('grab.verbose.spider.ng.parser')

class BaseParserSpider(BaseNGSpider):
    def load_new_response(self):
        try:
            response = self.response_queue.get(True, 0.1)
        except Empty:
            logger_verbose.debug('Response queue is empty.')
            response = None
        return response

    def run(self):
        SHOULD_WORK = True
        while SHOULD_WORK:
            response = self.load_new_response()

            if not response:
                self.wating_shutdown_event.set()
                if self.shutdown_event.is_set():
                    logger_verbose.debug('Got shutdown signal')
                    SHOULD_WORK = False
                else:
                    logger_verbose.debug('Shutdown event has not been set yet')
            else:
                if self.wating_shutdown_event.is_set():
                    self.wating_shutdown_event.clear()
                logger_verbose.debug('Got new response from response queue: %s' % response['task'].url)

                self.process_response_item(response)

        logger_verbose.debug('Work done')

    def process_response_item(self, response):
        self.result_cache = {
            'task': [],
            'data': [],
        }

        # Process the response
        handler_name = 'task_%s' % response['task'].name
        raw_handler_name = 'task_raw_%s' % response['task'].name
        try:
            raw_handler = getattr(self, raw_handler_name)
        except AttributeError:
            raw_handler = None

        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            handler = None

        if handler is None and raw_handler is None:
            raise SpiderError('No handler or raw handler defined for task %s' %\
                              response['task'].name)
        else:
            self.process_response(response, handler, raw_handler)

        for task in self.result_cache['task']:
            self.taskq.put(task)

    def add_task_handler(self, task, priority):
        self.result_cache['task'].append(task)

    def process_handler_result(self, result, task):
        """
        Process result produced by task handler.
        Result could be:
        * None
        * Task instance
        * Data instance.
        """

        if isinstance(result, Task):
            self.result_cache['task'].append(result)
        elif isinstance(result, Data):
            self.result_cache['data'].append(result)
        elif result is None:
            pass
        else:
            raise SpiderError('Unknown result type: %s' % result)
