import time
import Queue
import logging

from ..task import Task
from ..data import Data
from ..error import SpiderError
from .base import BaseNGSpider

class BaseManagerSpider(BaseNGSpider):
    def run(self):
        try:
            self.start_time = time.time()
            self.prepare()
            res_count = 0

            while True:
                try:
                    res = self.result_queue.get(block=True, timeout=2)
                except Queue.Empty:
                    #pass
                    res = None

                if res is None:
                    logging.error('res is None: stopping')
                    break

                if self.should_stop:
                    break

                if self.task_generator_enabled:
                    self.process_task_generator()

                for task in res['task_list']:
                    logging.debug('Processing task items from result queue')
                    self.add_task(task)

                for data in res['data_list']:
                    logging.debug('Processing data items from result queue')
                    #self.process_handler_result(data, task) 

        except KeyboardInterrupt:
            print '\nGot ^C signal. Stopping.'
            print self.render_stats()
            raise
        finally:
            # This code is executed when main cycles is breaked
            self.shutdown()

    def process_handler_result(self, result, task):
        """
        Process result produced by task handler.
        Result could be:
        * None
        * Task instance
        * Data instance.
        """

        if isinstance(result, Task):
            if not self.add_task(result):
                self.add_item('task-could-not-be-added', task.url)
        elif isinstance(result, Data):
            handler_name = 'data_%s' % result.name
            try:
                handler = getattr(self, handler_name)
            except AttributeError:
                raise SpiderError('No content handler for %s item', item)
            try:
                handler(result.item)
            except Exception, ex:
                self.process_handler_error(handler_name, ex, task)
        elif result is None:
            pass
        else:
            raise SpiderError('Unknown result type: %s' % result)


#def create_process(spider_cls, role, result_queue, *args, **kwargs):
    ## Create spider instance which will performe
    ## actions specific to given role
    #if role == 'manager':
        #class CustomManagerSpider(BaseManagerSpider, spider_cls):
            #pass
        #custom_cls = CustomManagerSpider
    #elif role == 'worker':
        #class CustomWorkerSpider(BaseWorkerSpider, spider_cls):
            #pass
        #custom_cls = CustomWorkerSpider
    #bot = custom_cls(result_queue, *args, **kwargs)

    ## Return Process object binded to the `bot.run` method
    #return Process(target=bot.run)
