import logging
import time

from ..task import Task
from ..data import Data
from ..error import SpiderError
from .base import BaseNGSpider

class BaseWorkerSpider(BaseNGSpider):
    def run(self):
        logger = logging.getLogger()
        handler = logging.FileHandler('/tmp/grab.worker.log', 'a')
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            self.start_time = time.time()
            self.setup_default_queue()
            self.prepare()

            for res_count, res in enumerate(self.get_next_response()):
                logging.error('worker iteration #%d' % res_count)
                if res is None:
                    logging.error('res is None')
                    break

                if self.should_stop:
                    break

                # Increase task counters
                self.inc_count('task')
                self.inc_count('task-%s' % res['task'].name)
                if (res['task'].network_try_count == 1 and
                    res['task'].task_try_count == 1):
                    self.inc_count('task-%s-initial' % res['task'].name)

                self.result_cache = {'task': [], 'data': []}

                # Process the response
                handler_name = 'task_%s' % res['task'].name
                raw_handler_name = 'task_raw_%s' % res['task'].name
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
                                      res['task'].name)
                else:
                    self.process_response(res, handler, raw_handler)

                res['task_list'] = self.result_cache['task']
                res['data_list'] = self.result_cache['data']
                self.result_queue.put(res)

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
            self.result_cache['task'].append(result)
        elif isinstance(result, Data):
            self.result_cache['data'].append(result)
        elif result is None:
            pass
        else:
            raise SpiderError('Unknown result type: %s' % result)
