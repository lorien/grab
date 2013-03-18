import logging
import time
from Queue import Empty

from ..task import Task
from ..data import Data
from ..error import SpiderError
from .base import BaseNGSpider
from ..base import TASK_QUEUE_TIMEOUT

from ..transport.multicurl import MulticurlTransport

logger = logging.getLogger('grab.spider.ng.downloader')
logger_verbose = logging.getLogger('grab.verbose.spider.ng.downloader')

class BaseDownloaderSpider(BaseNGSpider):
    def load_new_task(self):
        try:
            task = self.taskq.get(True, TASK_QUEUE_TIMEOUT)
        except Empty:
            logger_verbose.debug('Task queue is empty.')
            task = None
        return task

    def process_task_counters(self, task):
        task.network_try_count += 1
        if task.task_try_count == 0:
            task.task_try_count = 1

    def setup_grab_for_task(self, task):
        grab = self.create_grab_instance()
        if task.grab_config:
            grab.load_config(task.grab_config)
        else:
            grab.setup(url=task.url)

        # Generate new common headers
        grab.config['common_headers'] = grab.common_headers()
        if self.retry_rebuild_user_agent:
            grab.config['user_agent'] = None
        return grab

    def process_task(self, task):
        grab = self.setup_grab_for_task(task)
        grab_config_backup = grab.dump_config()

        cache_result = None
        if self.cache_allowed_for_task(task, grab):
            cache_result = self.query_cache(transport, task, grab,
                                            grab_config_backup)

        if cache_result:
            logger_verbose.debug('Task data is loaded from the cache. Yielding task result.')
            self.process_network_result(cache_result)
        else:
            if self.only_cache:
                logger.debug('Skipping network request to %s' % grab.config['url'])
            else:
                self.inc_count('request-network')
                self.change_proxy(task, grab)
                logger_verbose.debug('Submitting task to the transport layer')
                self.transport.process_task(task, grab, grab_config_backup)
                logger_verbose.debug('Asking transport layer to do something')
                self.transport.process_handlers()

    def run(self):
        self.transport = MulticurlTransport(self.thread_number)

        SHOULD_WORK = True
        while SHOULD_WORK:
            if self.transport.ready_for_task():
                logger_verbose.debug('Transport has free resources. Trying to add new task (if exists)')
                task = self.load_new_task()

                if not task:
                    if not self.transport.active_task_number():
                        logger_verbose.debug('Network transport has no active tasks')
                        self.wating_shutdown_event.set()
                        if self.shutdown_event.is_set():
                            logger_verbose.debug('Got shutdown signal')
                            SHOULD_WORK = False
                        else:
                            logger_verbose.debug('Shutdown event has not been set yet')
                    else:
                        logger_verbose.debug('Transport active tasks: %d' %
                                             self.transport.active_task_number())
                else:
                    if self.wating_shutdown_event.is_set():
                        self.wating_shutdown_event.clear()
                    logger_verbose.debug('Got new task from task queue: %s' % task)
                    self.process_task_counters(task)

                    if not self.check_task_limits(task):
                        logger_verbose.debug('Task %s is rejected due to limits' % task)
                    else:
                        self.process_task(task)

            logger_verbose.debug('Asking transport layer to do something')
            # Process active handlers
            self.transport.select(0.01)
            self.transport.process_handlers()

            logger_verbose.debug('Processing network results (if any).')
            # Iterate over network trasport ready results
            # Each result could be valid or failed
            # Result format: {ok, grab, grab_config_backup, task, emsg}
            for result in self.transport.iterate_results():
                if self.is_valid_for_cache(result):
                    self.cache.save_response(result['task'].url, result['grab'])
                self.process_network_result(result)
                self.inc_count('request')

        logger_verbose.debug('Work done')

    def process_network_result(self, res):
        # Increase stat counters
        self.inc_count('task')
        self.inc_count('task-%s' % res['task'].name)
        if (res['task'].network_try_count == 1 and
            res['task'].task_try_count == 1):
            self.inc_count('task-%s-initial' % res['task'].name)

        logger_verbose.debug('Submitting result for task %s to response queue' % res['task'])
        self.response_queue.put(self.prepare_response_queue_item(res))

    def prepare_response_queue_item(self, res):
        return res
