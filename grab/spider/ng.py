from multiprocessing import Process
import time
import Queue
import logging

from .base import Spider as TraditionalSpider, Task, Data, SpiderError

class Spider(TraditionalSpider):
    def __init__(self, role, result_queue, *args, **kwargs):
        self.role = role
        self.result_queue = result_queue
        super(Spider, self).__init__(*args, **kwargs)

    def setup_worker(self):
        pass

    def setup_manager(self):
        pass

    def run(self):
        """
        Main work cycle.
        """

        if self.role == 'manager':
            self.setup_manager()
            self.run_manager()

        if self.role == 'worker':
            self.setup_worker()
            self.run_worker()

    def prepare_before_run(self):
        """
        Configure all things required to begin
        executing tasks in main `run` method.
        """

        # If queue is still not configured
        # then configure it with default backend
        if self.taskq is None:
            self.log_verbose('Settings default mongo task queue')
            self.setup_queue(backend='mongo', database='ng_queue',
                             queue_name='task')

        self.prepare()

        if self.role == 'manager':
            self.log_verbose('Creating task generator object')
            # Init task generator
            self.task_generator_object = self.task_generator()
            self.task_generator_enabled = True

            self.log_verbose('Processing initial urls')
            self.load_initial_urls()

            self.log_verbose('Asking task generator to generate '\
                             'initial portion of tasks')
            # Initial call to task generator
            # before main cycle
            self.process_task_generator()

    def run_manager(self):
        try:
            self.start_time = time.time()
            self.prepare_before_run()
            res_count = 0

            while True:
            #for res_count, res in enumerate(self.get_next_response()):
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

    def run_worker(self):
        logger = logging.getLogger()
        handler = logging.FileHandler('/tmp/grab.worker.log', 'a')
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            self.start_time = time.time()
            self.prepare_before_run()

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

        if self.role == 'manager':
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

        if self.role == 'worker':
            if isinstance(result, Task):
                self.result_cache['task'].append(result)
            elif isinstance(result, Data):
                self.result_cache['data'].append(result)
            elif result is None:
                pass
            else:
                raise SpiderError('Unknown result type: %s' % result)


def create_process(spider_cls, role, result_queue, *args, **kwargs):
    # Create spider instance which will performe
    # actions specific to given role
    bot = spider_cls(role, result_queue, *args, **kwargs)

    # Return Process object binded to the `bot.run` method
    return Process(target=bot.run)
