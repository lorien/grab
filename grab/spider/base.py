"""
Global TODO:
* make task_%s_preprocess methods
"""
from __future__ import absolute_import
import types
import signal
import inspect
import traceback
import logging
from collections import defaultdict
import os
import time
import json
import cPickle as pickle
import anydbm
import multiprocessing
import zlib
from hashlib import sha1
from urlparse import urljoin
from random import randint

import Queue
from ..base import GLOBAL_STATE, Grab
from .error import (SpiderError, SpiderMisuseError, FatalError,
                    StopTaskProcessing)
from .task import Task, NullTask
from .data import Data
from .pattern import SpiderPattern
from .stat  import SpiderStat
from .transport.multicurl import MulticurlTransport
from ..proxylist import ProxyList

DEFAULT_TASK_PRIORITY = 100
RANDOM_TASK_PRIORITY_RANGE = (50, 100)
TASK_QUEUE_TIMEOUT = 0.01
NULL = object()

logger = logging.getLogger('grab.spider.base')
logger_verbose = logging.getLogger('grab.spider.base.verbose')
# If you need verbose logging just
# change logging level of that logger
logger_verbose.setLevel(logging.FATAL)

class Spider(SpiderPattern, SpiderStat):
    """
    Asynchronious scraping framework.
    """

    # You can define here some urls and initial tasks
    # with name "initial" will be created from these
    # urls
    # If the logic of generating initial tasks is complex
    # then consider to use `task_generator` method instead of
    # `initial_urls` attribute
    initial_urls = None

    # The base url which is used to resolve all relative urls
    # The resolving takes place in `add_task` method
    base_url = None

    middlewares = []
    middleware_points = {
        'response': [],
    }

    def __init__(self, thread_number=3,
                 network_try_limit=10, task_try_limit=10,
                 debug_error=False,
                 request_pause=NULL,
                 priority_mode='random',
                 meta=None,
                 only_cache=False,
                 config=None,
                 slave=False,
                 max_task_generator_chunk=None,
                 ):
        """
        Arguments:
        * thread-number - Number of concurrent network streams
        * network_try_limit - How many times try to send request
            again if network error was occuried, use 0 to disable
        * network_try_limit - Limit of tries to execute some task
            this is not the same as network_try_limit
            network try limit limits the number of tries which
            are performed automaticall in case of network timeout
            of some other physical error
            but task_try_limit limits the number of attempts which
            are scheduled manually in the spider business logic
        * priority_mode - could be "random" or "const"
        * meta - arbitrary user data
        * retry_rebuid_user_agent - generate new random user-agent for each
            network request which is performed again due to network error
        """

        self.slave = slave

        self.max_task_generator_chunk = max_task_generator_chunk
        self.timers = {}
        self.time_points = {}
        self.start_timer('total')
        if config is not None:
            self.config = config
        else:
            self.config = {}

        self.taskq = None

        if meta:
            self.meta = meta
        else:
            self.meta = {}

        self.task_generator_enabled = False
        self.only_cache = only_cache
        self.thread_number = thread_number
        self.counters = defaultdict(int)
        self.grab_config = {}
        self.items = {}
        self.task_try_limit = task_try_limit
        self.network_try_limit = network_try_limit
        if priority_mode not in ['random', 'const']:
            raise SpiderMisuseError('Value of priority_mode option should be "random" or "const"')
        else:
            self.priority_mode = priority_mode
        try:
            signal.signal(signal.SIGUSR1, self.sigusr1_handler)
        except (ValueError, AttributeError):
            pass
        try:
            signal.signal(signal.SIGUSR2, self.sigusr2_handler)
        except (ValueError, AttributeError):
            pass
        self.debug_error = debug_error

        # Initial cache-subsystem values
        self.cache_enabled = False
        self.cache = None

        self.work_allowed = True
        if request_pause is not NULL:
            logging.error('Option `request_pause` is deprecated and is not supported anymore')

        self.proxylist_enabled = None
        self.proxylist = None
        self.proxy = None
        self.proxy_auto_change = False

    def setup_middleware(self, middleware_list):
        for item in middleware_list:
            self.middlewares.append(item)
            mod_path, cls_name = item.rsplit('.', 1)
            mod = __import__(mod_path, None, None, ['foo'])
            cls = getattr(mod, cls_name)
            mid = cls()
            if hasattr(mid, 'process_response'):
                self.middleware_points['response'].append(mid)

    def setup_cache(self, backend='mongo', database=None, use_compression=True, **kwargs):
        if database is None:
            raise SpiderMisuseError('setup_cache method requires database option')
        self.cache_enabled = True
        mod = __import__('grab.spider.cache_backend.%s' % backend,
                         globals(), locals(), ['foo'])
        self.cache = mod.CacheBackend(database=database, use_compression=use_compression,
                                      spider=self, **kwargs)

    def setup_queue(self, backend='memory', **kwargs):
        logger.debug('Using %s backend for task queue' % backend)
        mod = __import__('grab.spider.queue_backend.%s' % backend,
                         globals(), locals(), ['foo'])
        self.taskq = mod.QueueBackend(**kwargs)

    def prepare(self):
        """
        You can do additional spider customizatin here
        before it has started working. Simply redefine
        this method in your Spider class.
        """

    def sigusr1_handler(self, signal, frame):
        """
        Catches SIGUSR1 signal and dumps current state
        to temporary file
        """

        with open('/tmp/spider.state', 'w') as out:
            out.write(self.render_stats())

    def sigusr2_handler(self, signal, frame):
        """
        Catches SIGUSR1 signal and shutdowns spider.
        """
        
        logging.error('Received SIGUSR2 signal. Doing shutdown')
        self.stop()

    def setup_grab(self, **kwargs):
        self.grab_config.update(**kwargs)

    def check_task_limits(self, task):
        """
        Check that network/try counters are OK.

        If one of counter is invalid then display error
        and try to call fallback handler.
        """

        is_valid = True

        if not self.config.get('task_%s' % task.name, True):
            logger.debug('Task %s disabled via config' % task.name)
            is_valid = False

        elif task.task_try_count > self.task_try_limit:
            logger.debug('Task tries (%d) ended: %s / %s' % (
                          self.task_try_limit, task.name, task.url))
            self.add_item('too-many-task-tries', task.url)
            is_valid = False

        elif task.network_try_count > self.network_try_limit:
            logger.debug('Network tries (%d) ended: %s / %s' % (
                          self.network_try_limit, task.name, task.url))
            self.add_item('too-many-network-tries', task.url)
            is_valid = False

        return is_valid

    def check_task_limits_deprecated(self, task):
        is_valid = self.check_task_limits(task)

        if not is_valid:
            try:
                fallback_handler = getattr(self, 'task_%s_fallback' % task.name)
            except AttributeError:
                pass
            else:
                fallback_handler(task)

        return is_valid

    def generate_task_priority(self):
        if self.priority_mode == 'const':
            return DEFAULT_TASK_PRIORITY
        else:
            return randint(*RANDOM_TASK_PRIORITY_RANGE)

    def add_task_handler(self, task):
        self.taskq.put(task, task.priority)

    def add_task(self, task):
        """
        Add task to the task queue.

        Abort the task which was restarted too many times.
        """

        if self.taskq is None:
            raise SpiderMisuseError('You should configure task queue before adding tasks. Use `setup_queue` method.')
        if task.priority is None or not task.priority_is_custom:
            task.priority = self.generate_task_priority()
            task.priority_is_custom = False
        else:
            task.priority_is_custom = True

        if not isinstance(task, NullTask):
            if (not task.url.startswith('http://') and not task.url.startswith('https://')
                and not task.url.startswith('ftp://')):
                if self.base_url is None:
                    raise SpiderMisuseError('Could not resolve relative URL because base_url is not specified')
                else:
                    task.url = urljoin(self.base_url, task.url)
                    # If task has grab_config object then update it too
                    if task.grab_config:
                        task.grab_config['url'] = task.url

        is_valid = self.check_task_limits_deprecated(task)
        if is_valid:
            # TODO: keep original task priority if it was set explicitly
            self.add_task_handler(task)
        else:
            self.add_item('task-could-not-be-added', task.url)
        return is_valid

    def load_initial_urls(self):
        """
        Create initial tasks from `self.initial_urls`.

        Tasks are created with name "initial".
        """

        if self.initial_urls:
            for url in self.initial_urls:
                self.add_task(Task('initial', url=url))

    def setup_default_queue(self):
        """
        If task queue is not configured explicitly
        then create task queue with default parameters

        This method is not the same as `self.setup_queue` because
        `self.setup_queue` works by default with in-memory queue.
        You can override `setup_default_queue` in your custom
        Spider and use other storage engines for you
        default task queue.
        """

        # If queue is still not configured
        # then configure it with default backend
        if self.taskq is None:
            self.setup_queue()
        
    def process_task_generator(self):
        """
        Load new tasks from `self.task_generator_object`
        Create new tasks.

        If task queue size is less than some value
        then load new tasks from tasks file.
        """

        if self.task_generator_enabled:
            if hasattr(self.taskq, 'qsize'):
                qsize = self.taskq.qsize()
            else:
                qsize = self.taskq.size()
            if self.max_task_generator_chunk is not None:
                min_limit = min(self.max_task_generator_chunk,
                                self.thread_number * 10)
            else:
                min_limit = self.thread_number * 10
            if qsize < min_limit:
                logger_verbose.debug('Task queue contains less tasks than limit. Tryring to add new tasks')
                try:
                    for x in xrange(min_limit - qsize):
                        item = self.task_generator_object.next()
                        logger_verbose.debug('Found new task. Adding it')
                        self.add_task(item)
                except StopIteration:
                    # If generator have no values to yield
                    # then disable it
                    logger_verbose.debug('Task generator has no more tasks. Disabling it')
                    self.task_generator_enabled = False

    def init_task_generators(self):
        """
        Process `initial_urls` and `task_generator`.
        Generate first portion of tasks.

        TODO: task generator should work in separate OS process
        """

        self.task_generator_object = self.task_generator()
        self.task_generator_enabled = True

        self.load_initial_urls()

        # Initial call to task generator
        # before main cycle
        self.process_task_generator()

    def load_new_task(self):
        start = time.time()
        while True:
            try:
                with self.save_timer('task_queue'):
                    return self.taskq.get(TASK_QUEUE_TIMEOUT)
            except Queue.Empty:
                if not self.slave:
                    logger_verbose.debug('Task queue is empty.')
                    return None
                else:
                    # Temporarly hack which force slave crawler
                    # to wait 2 seconds for new tasks, this solves
                    # the problem that sometimes slave crawler stop
                    # its work because it could not receive new
                    # tasks immediatelly
                    if not self.transport.active_task_number():
                        if time.time() - start < 5:
                            time.sleep(0.1)
                            logger.debug('Slave sleeping')
                        else:
                            break
                    else:
                        break

        logger_verbose.debug('Task queue is empty.')
        return None

    def process_task_counters(self, task):
        task.network_try_count += 1
        if task.task_try_count == 0:
            task.task_try_count = 1

    def create_grab_instance(self):
        return Grab(**self.grab_config)

    def setup_grab_for_task(self, task):
        grab = self.create_grab_instance()
        if task.grab_config:
            grab.load_config(task.grab_config)
        else:
            grab.setup(url=task.url)

        # Generate new common headers
        grab.config['common_headers'] = grab.common_headers()
        return grab

    def is_task_cacheable(self, task, grab):
        if (# cache is disabled for all tasks
            not self.cache_enabled
            # cache data should be refreshed
            or task.get('refresh_cache', False)
            # cache could not be used
            or task.get('disable_cache', False)
            # request type is not cacheable
            or grab.detect_request_method() != 'GET'):
            return False
        else:
            return True

    def load_task_from_cache(self, transport, task, grab, grab_config_backup):
        cache_item = self.cache.get_item(grab.config['url'],
                                         timeout=task.cache_timeout)
        if cache_item is None:
            return None
        else:
            with self.save_timer('cache.read.prepare_request'):
                grab.prepare_request()
            with self.save_timer('cache.read.load_response'):
                self.cache.load_response(grab, cache_item)

            grab.log_request('CACHED')
            self.inc_count('request')
            self.inc_count('request-cache')

            return {'ok': True, 'grab': grab,
                   'grab_config_backup': grab_config_backup,
                   'task': task, 'emsg': None}

    def valid_response_code(self, code, task):
        """
        Answer the question: if the response could be handled via
        usual task handler or the task faield and should be processed as error.
        """

        return (code < 400 or code == 404 or
                code in task.valid_status)

    def process_handler_error(self, func_name, ex, task, error_tb=None):
        self.inc_count('error-%s' % ex.__class__.__name__.lower())

        if error_tb:
            logger.error('Error in %s function' % func_name)
            logger.error(error_tb)
        else:
            logger.error('Error in %s function' % func_name,
                          exc_info=ex)

        # Looks strange but I really have some problems with
        # serializing exception into string
        try:
            ex_str = unicode(ex)
        except TypeError:
            try:
                ex_str = unicode(ex, 'utf-8', 'ignore')
            except TypeError:
                ex_str = str(ex)

        self.add_item('fatal', '%s|%s|%s' % (ex.__class__.__name__,
                                             ex_str, task.url))
        if self.debug_error:
            # TODO: open pdb session in the place where exception
            # was raised
            import pdb; pdb.set_trace()

        if isinstance(ex, FatalError):
            raise

    def process_handler_result(self, result, task):
        """
        Process result received from the task handler.

        Result could be:
        * None
        * Task instance
        * Data instance.
        """

        if isinstance(result, Task):
            self.add_task(result)
        elif isinstance(result, Data):
            handler_name = 'data_%s' % result.name
            try:
                handler = getattr(self, handler_name)
            except AttributeError:
                raise SpiderError('No content handler for %s item' % result.name)
            try:
                handler(result.item)
            except Exception, ex:
                self.process_handler_error(handler_name, ex, task)
        elif result is None:
            pass
        else:
            raise SpiderError('Unknown result type: %s' % result)

    def execute_task_handler(self, res, handler, raw_handler=None):
        """
        Apply `handler` function to the network result.

        If network result is failed then submit task again
        to the network task queue.
        """

        process_handler = True
        if raw_handler is not None:
            process_handler = raw_handler(res)

        if not process_handler:
            return

        if handler is None:
            raise SpiderMisuseError('Handler is not defined for task %s' % res['task'].name)

        try:
            handler_name = handler.__name__
        except AttributeError:
            handler_name = 'NONE'

        if res['ok'] and self.valid_response_code(res['grab'].response.code,
                                                  res['task']):
            try:
                with self.save_timer('response_handler'):
                    with self.save_timer('response_handler.%s' % handler_name):
                        result = handler(res['grab'], res['task'])
                        if isinstance(result, types.GeneratorType):
                            for item in result:
                                self.process_handler_result(item, res['task'])
                        else:
                            self.process_handler_result(result, res['task'])
            except Exception, ex:
                self.process_handler_error(handler_name, ex, res['task'])
            else:
                self.inc_count('task-%s-ok' % res['task'].name)
        else:
            # Log the error
            if res['ok']:
                msg = res['emsg'] = 'HTTP %s' % res['grab'].response.code
            else:
                msg = res['emsg']
            self.inc_count('network-error-%s' % res['emsg'][:20])
            logger.error(msg)

            # Try to repeat the same network query
            if self.network_try_limit > 0:
                task = res['task']
                task.refresh_cache = True
                # Should use task.grab_config or backup of grab_config
                task.setup_grab_config(res['grab_config_backup'])
                self.add_task(task)
            # TODO: allow to write error handlers
    

    def process_network_result(self, res):
        """
        Handle result received from network transport of
        from the cache layer.

        Find handler function for that task and call it.
        """

        # Increase stat counters
        self.inc_count('request-processed')
        self.inc_count('task')
        self.inc_count('task-%s' % res['task'].name)
        if (res['task'].network_try_count == 1 and
            res['task'].task_try_count == 1):
            self.inc_count('task-%s-initial' % res['task'].name)

        stop = False
        for mid in self.middleware_points['response']:
            try:
                mid_response = mid.process_response(self, res)
            except StopTaskProcessing:
                logger.debug('Got StopTaskProcessing exception')
                stop = True
                break
            else:
                if isinstance(mid_response, Task):
                    logger.debug('Got task from middleware')
                    self.add_task(mid_response)
                    stop = True
                    break
                elif mid_response is None:
                    pass
                else:
                    raise Exception('Unknown response from middleware %s' % mid)

        if stop:
            return

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
            self.execute_task_handler(res, handler, raw_handler)

    def change_proxy(self, task, grab):
        """
        Assign new proxy from proxylist to the task.
        """

        if task.use_proxylist and self.proxylist_enabled:
            if self.proxy_auto_change:
                self.proxy = self.proxylist.get_random()
            if self.proxy:
                proxy, proxy_userpwd, proxy_type = self.proxy
                grab.setup(proxy=proxy, proxy_userpwd=proxy_userpwd,
                           proxy_type=proxy_type)

    def process_new_task(self, task):
        """
        Handle new task.

        1) Setup Grab object for that task
        2) Try to load task from the cache
        3) If no cached data then submit task to network transport
        """

        grab = self.setup_grab_for_task(task)
        grab_config_backup = grab.dump_config()

        cache_result = None
        if self.is_task_cacheable(task, grab):
            with self.save_timer('cache'):
                with self.save_timer('cache.read'):
                    cache_result = self.load_task_from_cache(
                        self.transport, task, grab, grab_config_backup)

        if cache_result:
            logger_verbose.debug('Task data is loaded from the cache. Yielding task result.')
            self.process_network_result(cache_result)
        else:
            if self.only_cache:
                logger.debug('Skipping network request to %s' % grab.config['url'])
            else:
                self.inc_count('request-network')
                self.change_proxy(task, grab)
                with self.save_timer('network_transport'):
                    logger_verbose.debug('Submitting task to the transport layer')
                    self.transport.process_task(task, grab, grab_config_backup)
                    logger_verbose.debug('Asking transport layer to do something')
                    self.transport.process_handlers()

    def is_valid_for_cache(self, res):
        """
        Check if network transport result could
        be saved to cache layer.

        res: {ok, grab, grab_config_backup, task, emsg}
        """


        if res['ok']:
            if self.cache_enabled:
                if res['grab'].request_method == 'GET':
                    if not res['task'].get('disable_cache'):
                        if self.valid_response_code(res['grab'].response.code, res['task']):
                            return True
        return False

    def stop(self):
        """
        This method set internal flag which signal spider
        to stop processing new task and shuts down.
        """

        self.work_allowed = False

    def run(self):
        """
        Main method. All work is done here.
        """

        self.start_timer('total')

        self.transport = MulticurlTransport(self.thread_number)

        try:
            self.setup_default_queue()
            self.prepare()

            self.start_timer('task_generator')
            if not self.slave:
                self.init_task_generators()
            self.stop_timer('task_generator')

            while self.work_allowed:
                self.start_timer('task_generator')
                if self.task_generator_enabled:
                    self.process_task_generator()
                self.stop_timer('task_generator')

                if self.transport.ready_for_task():
                    logger_verbose.debug('Transport has free resources. '\
                                         'Trying to add new task (if exists)')

                    # Try five times to get new task and proces task generator
                    # because slave parser could agressively consume
                    # tasks from task queue
                    for x in xrange(5):
                        task = self.load_new_task()
                        if not task:
                            if not self.transport.active_task_number():
                                self.process_task_generator()
                        else:
                            break

                    if not task:
                        if not self.transport.active_task_number():
                            logger_verbose.debug('Network transport has no active tasks')
                            #self.wating_shutdown_event.set()
                            if True:#self.shutdown_event.is_set():
                                #logger_verbose.debug('Got shutdown signal')
                                self.stop()
                            #else:
                                #logger_verbose.debug('Shutdown event has not been set yet')
                        else:
                            logger_verbose.debug('Transport active tasks: %d' %
                                                 self.transport.active_task_number())
                    elif isinstance(task, NullTask):
                        logger_verbose.debug('Got NullTask')
                        if not self.transport.active_task_number():
                            if task.sleep:
                                logger.debug('Got NullTask with sleep instruction. Sleeping for %.2f seconds' % task.sleep)
                                time.sleep(task.sleep)
                    else:
                        #if self.wating_shutdown_event.is_set():
                            #self.wating_shutdown_event.clear()
                        logger_verbose.debug('Got new task from task queue: %s' % task)
                        self.process_task_counters(task)

                        if not self.check_task_limits(task):
                            logger_verbose.debug('Task %s is rejected due to limits' % task.name)
                        else:
                            self.process_new_task(task)

                with self.save_timer('network_transport'):
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
                        with self.save_timer('cache'):
                            with self.save_timer('cache.write'):
                                self.cache.save_response(result['task'].url, result['grab'])
                    self.process_network_result(result)
                    self.inc_count('request')

            logger_verbose.debug('Work done')
        except KeyboardInterrupt:
            print '\nGot ^C signal. Stopping.'
            raise
        finally:
            # This code is executed when main cycles is breaked
            self.stop_timer('total')
            self.shutdown()

    def load_proxylist(self, source, source_type, proxy_type='http',
                       auto_init=True, auto_change=True,
                       **kwargs):
        self.proxylist = ProxyList(source, source_type, proxy_type=proxy_type, **kwargs)

        self.proxylist_enabled = True
        self.proxy = None
        if not auto_change and auto_init:
            self.proxy = self.proxylist.get_random()
        self.proxy_auto_change = auto_change

    # ****************
    # Abstract methods
    # ****************

    def shutdown(self):
        """
        You can override this method to do some final actions
        after parsing has been done.
        """

        logger.debug('Job done!')

    def task_generator(self):
        """
        You can override this method to load new tasks smoothly.

        It will be used each time as number of tasks
        in task queue is less then number of threads multiplied on 2
        This allows you to not overload all free memory if total number of
        tasks is big.
        """

        if False:
            # Some magic to make this function empty generator
            yield ':-)'
        return
