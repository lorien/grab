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
from .error import SpiderError, SpiderMisuseError, FatalError
from .task import Task
from .data import Data
from .pattern import SpiderPattern
from .stat  import SpiderStat
from .transport.multicurl import MulticurlTransport
from .transport.threadpool import ThreadPoolTransport

DEFAULT_TASK_PRIORITY = 100
RANDOM_TASK_PRIORITY_RANGE = (80, 100)
TASK_QUEUE_TIMEOUT = 0.01

logger = logging.getLogger('grab.spider.base')

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

    def __init__(self, thread_number=3, request_limit=None,
                 network_try_limit=10, task_try_limit=10,
                 debug_error=False,
                 use_cache=None,
                 use_cache_compression=None,
                 cache_db = None,
                 log_taskname=False,
                 request_pause=0,
                 priority_mode='random',
                 meta=None,
                 ):
        """
        Arguments:
        * thread-number - Number of concurrent network streams
        * request_limit - Limit number of all network requests
            Useful for debugging
        * network_try_limit - How many times try to send request
            again if network error was occuried, use 0 to disable
        * network_try_limit - Limit of tries to execute some task
            this is not the same as network_try_limit
            network try limit limits the number of tries which
            are performed automaticall in case of network timeout
            of some other physical error
            but task_try_limit limits the number of attempts which
            are scheduled manually in the spider business logic
        * request_pause - amount of time on which the main `run` cycle should
            pause the activity of spider. By default it is equal to zero. You
            can use this option to slow down the spider speed (also you can use
            `thread_number` option). The value of `request_pause` could be float.
        * priority_mode - could be "random" or "const"
        * meta - arbitrary user data
        """

        self.taskq = None

        if use_cache is not None:
            logger.error('use_cache argument is depricated. Use setup_cache method.')
            use_cache = False
        if use_cache_compression is not None:
            logger.error('use_cache_compression argument is depricated. Use setup_cache method.')
            use_cache_compression = False
        if cache_db is not None:
            logger.error('cache_db argument is depricated. Use setup_cache method.')
        # TODO: Remove
        if use_cache:
            self.setup_cache(backend='mongo', database=cache_db,
                             use_compression=use_cache_compression)

        if meta:
            self.meta = meta
        else:
            self.meta = {}

        self.thread_number = thread_number
        self.request_limit = request_limit
        self.counters = defaultdict(int)
        self.grab_config = {}
        self.proxylist_config = None
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
        self.debug_error = debug_error

        # Initial cache-subsystem values
        self.cache_enabled = False
        self.cache = None

        self.log_taskname = log_taskname
        self.should_stop = False
        self.request_pause = request_pause

    def setup_cache(self, backend='mongo', database=None, use_compression=True, **kwargs):
        if database is None:
            raise SpiderMisuseError('setup_cache method requires database option')
        self.cache_enabled = True
        mod = __import__('grab.spider.cache_backend.%s' % backend,
                         globals(), locals(), ['foo'])
        self.cache = mod.CacheBackend(database=database, use_compression=use_compression)

    def setup_queue(self, backend='memory', database=None, **kwargs):
        mod = __import__('grab.spider.queue_backend.%s' % backend,
                         globals(), locals(), ['foo'])
        self.taskq = mod.QueueBackend(database=database, **kwargs)

    def prepare(self):
        """
        You can do additional spider customizatin here
        before it has started working.
        """

    def sigusr1_handler(self, signal, frame):
        """
        Catches SIGUSR1 signal and dumps current state
        to temporary file
        """

        with open('/tmp/spider.state', 'w') as out:
            out.write(self.render_stats())

    def setup_grab(self, **kwargs):
        self.grab_config = kwargs

    def load_initial_urls(self):
        """
        Create initial tasks from `self.initial_urls`.

        Tasks are created with name "initial".
        """

        if self.initial_urls:
            for url in self.initial_urls:
                self.add_task(Task('initial', url=url))

    def prepare_before_run(self):
        """
        Configure all things required to begin
        executing tasks in main `run` method.
        """

        # If queue is still not configured
        # then configure it with default backend
        if self.taskq is None:
            self.setup_queue()

        self.prepare()

        # Init task generator
        self.task_generator_object = self.task_generator()
        self.task_generator_enabled = True

        self.load_initial_urls()

        # Initial call to task generator
        # before main cycle
        self.process_task_generator()

    def run(self):
        """
        Main work cycle.
        """

        try:
            self.start_time = time.time()
            self.prepare_before_run()

            for res_count, res in enumerate(self.get_next_response()):
                if res_count > 0 and self.request_pause > 0:
                    time.sleep(self.request_pause)

                if res is None:
                    break

                if self.should_stop:
                    break

                if self.task_generator_enabled:
                    self.process_task_generator()

                # Increase task counters
                self.inc_count('task')
                self.inc_count('task-%s' % res['task'].name)
                if (res['task'].network_try_count == 1 and
                    res['task'].task_try_count == 1):
                    self.inc_count('task-%s-initial' % res['task'].name)

                # Log task name
                if self.log_taskname:
                    status = 'OK' if res['ok'] else 'FAIL'
                    logger.error('TASK: %s - %s' % (res['task'].name, status))

                # Process the response
                handler_name = 'task_%s' % res['task'].name
                try:
                    handler = getattr(self, handler_name)
                except AttributeError:
                    raise SpiderError('Task handler does not exist: %s' % handler_name)
                else:
                    self.process_response(res, handler)

        except KeyboardInterrupt:
            print '\nGot ^C signal. Stopping.'
            print self.render_stats()
        finally:
            # This code is executed when main cycles is breaked
            self.shutdown()

    def valid_response_code(self, code, task):
        """
        Answer the question: if the response could be handled via
        usual task handler or the task faield and should be processed as error.
        """

        return (code < 400 or code == 404 or
                code in task.valid_status)

    def process_response(self, res, handler):
        """
        Run the handler associated with the task for which the response
        was received.
        """

        if res['ok'] and self.valid_response_code(res['grab'].response.code,
                                                  res['task']):
            try:
                result = handler(res['grab'], res['task'])
                if isinstance(result, types.GeneratorType):
                    for item in result:
                        self.process_handler_result(item, res['task'])
                else:
                    self.process_handler_result(result, res['task'])
            except Exception, ex:
                self.process_handler_error(handler.__name__, ex, res['task'])
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
                # GRAB CLONE ISSUE
                # Should use task.grab_config or backup of grab_config
                task.grab = res['grab_config_backup']
                self.add_task(task)
            # TODO: allow to write error handlers
    
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

    def add_task(self, task):
        """
        Add task to the task queue.

        Abort the task which was restarted too many times.
        """

        if self.taskq is None:
            raise SpiderMisuseError('You should configure task queue before adding tasks. Use `setup_queue` method.')
        if task.priority is None:
            if self.priority_mode == 'const':
                task.priority = DEFAULT_TASK_PRIORITY
            else:
                task.priority = randint(*RANDOM_TASK_PRIORITY_RANGE)

        if (not task.url.startswith('http://') and not task.url.startswith('https://')
            and not task.url.startswith('ftp://')):
            if self.base_url is None:
                raise SpiderMisuseError('Could not resolve relative URL because base_url is not specified')
            else:
                task.url = urljoin(self.base_url, task.url)
                # If task has grab_config object then update it too
                if task.grab_config:
                    task.grab_config['url'] = task.url

        is_valid = self.check_task_limits(task)
        if is_valid:
            self.taskq.put((task.priority, task))
        return is_valid

    def check_task_limits(self, task):
        """
        Check that network/try counters are OK.

        If one of counter is invalid then display error
        and try to call fallback handler.
        """

        is_valid = True
        if task.task_try_count > self.task_try_limit:
            logger.debug('Task tries (%d) ended: %s / %s' % (
                          self.task_try_limit, task.name, task.url))
            self.add_item('too-many-task-tries', task.url)
            is_valid = False
        elif task.network_try_count > self.network_try_limit:
            logger.debug('Network tries (%d) ended: %s / %s' % (
                          self.network_try_limit, task.name, task.url))
            self.add_item('too-many-network-tries', task.url)
            is_valid = False

        if not is_valid:
            try:
                fallback_handler = getattr(self, 'task_%s_fallback' % task.name)
            except AttributeError:
                pass
            else:
                fallback_handler(task)

        return is_valid

    def get_next_response(self):
        """
        Use async transport to download tasks.
        If it yields None then scraping process should stop.

        # TODO: this method is TOO big
        """ 

        transport = MulticurlTransport(self.thread_number)

        # This is infinite cycle
        # You can break it only from outside code which
        # iterates over result of this method
        # This cyle is breaked from inside only
        # if self.request_limit is reached
        while True:

            cached_request = None

            # while transport is ready for new requests
            while transport.ready_for_task():
                # If request number limit is reached
                # then do not add new tasks and yield None (which will stop all)
                # when length of freelist (number of free workers)
                # will become equal to number of threads (total number of workers)
                # Worker is just a network stream
                if (self.request_limit is not None and
                    self.counters['request'] >= self.request_limit):

                    logger.debug('Request limit is reached: %s' %
                                 self.request_limit)
                    if not transport.active_task_number():
                        yield None
                    else:
                        print 'break'
                        break
                else:
                    try:
                        priority, task = self.taskq.get(True, TASK_QUEUE_TIMEOUT)
                    except Queue.Empty:
                        # If All handlers are free and no tasks in queue
                        # yield None signal
                        if not transport.active_task_number():
                            yield None
                        else:
                            break
                    else:
                        task.network_try_count += 1
                        if task.task_try_count == 0:
                            task.task_try_count = 1

                        if not self.check_task_limits(task):
                            continue

                        grab = self.create_grab_instance()
                        if task.grab_config:
                            grab.load_config(task.grab_config)
                        else:
                            grab.setup(url=task.url)

                        grab_config_backup = grab.dump_config()

                        if (self.cache_enabled
                            and not task.get('refresh_cache', False)
                            and not task.get('disable_cache', False)
                            and grab.detect_request_method() == 'GET'):

                            cache_item = self.cache.get_item(grab.config['url'])
                            if cache_item:
                                transport.repair_grab(grab)
                                # GRAB CLONE ISSUE
                                cached_request = (grab, task, cache_item)
                                grab.prepare_request()
                                grab.log_request('CACHED')
                                self.inc_count('request-cache')

                                # break from prepare-request cycle
                                # and go to process-response code
                                break

                        self.inc_count('request-network')
                        if task.use_proxylist and self.proxylist_config:
                            args, kwargs = self.proxylist_config
                            grab.setup_proxylist(*args, **kwargs)

                        transport.process_task(task, grab, grab_config_backup)

            # If real network requests were fired
            # when wait for some result
            # TODO: probably this code should go after prcessing
            # of results from the cache
            transport.wait_result()

            if cached_request:
                # GRAB CLONE ISSUE
                grab, task, cache_item = cached_request
                self.cache.load_response(grab, cache_item)

                # GRAB CLONE ISSUE
                yield {'ok': True, 'grab': grab,
                       'grab_config_backup': grab_config_backup,
                       'task': task, 'emsg': None}
                self.inc_count('request')

            # Iterate over network trasport ready results
            # Each result could be valid or failed
            # Result format: {ok, grab, grab_config_backup, task, emsg}
            for result in transport.iterate_results():
                yield self.process_transport_result(result)
                self.inc_count('request')

            # Calling special async magic function
            # to do async things
            transport.select()

    def process_transport_result(self, res):
        """
        Process asyncronous transport result

        res: {ok, grab, grab_config_backup, task, emsg}
        """


        if (res['ok'] and self.cache_enabled and res['grab'].request_method == 'GET'
            and not res['task'].get('disable_cache')):
            if self.valid_response_code(res['grab'].response.code, res['task']):
                self.cache.save_response(res['task'].url, res['grab'])

        return res

    def shutdown(self):
        """
        You can override this method to do some final actions
        after parsing has been done.
        """

        logger.debug('Job done!')

    def setup_proxylist(self, *args, **kwargs):
        """
        Save proxylist config which will be later passed to Grab
        constructor.
        """

        self.proxylist_config = (args, kwargs)

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

    def process_task_generator(self):
        """
        Load new tasks from `self.task_generator_object`
        Create new tasks.

        If task queue size is less than some value
        then load new tasks from tasks file.
        """

        qsize = self.taskq.qsize()
        min_limit = self.thread_number * 2
        if qsize < min_limit:
            try:
                for x in xrange(min_limit - qsize):
                    self.add_task(self.task_generator_object.next())
            except StopIteration:
                # If generator have no values to yield
                # then disable it
                self.task_generator_enabled = False

    def create_grab_instance(self):
        return Grab(**self.grab_config)

    def stop(self):
        """
        Stop main loop.
        """

        self.should_stop = True

    @classmethod
    def init_with_config(cls, modname):
        """
        This method create spider instance and configure it
        with options found in given config module.
        
        Args:
            :modname string: name of module with settings
        """

        # Load key, value dict from config module
        config = __import__(modname, fromlist=[''])
        config_dict = {}
        for key in dir(config):
            config_dict[key.lower()] = getattr(config, key)

        # Find names of arguments of __init__ method
        arg_names = inspect.getargspec(getattr(cls, '__init__'))[0]
        arg_names = [x.lower() for x in arg_names]

        # Find __init__ arguments in config module
        kwargs = {}
        for name in arg_names:
            if name in config_dict:
                kwargs[name] = config_dict[name]

        # Create Spider instance
        obj = cls(**kwargs)

        # Configure proxy list
        if 'proxylist' in config_dict:
            obj.setup_proxylist(**config_dict['proxylist'])

        return obj

    def dump_title(self, grab):
        print grab.xpath_text('//title', 'N/A')
