from __future__ import absolute_import
import types
import logging
import time
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin
from random import randint
try:
    import Queue as queue
except ImportError:
    import queue
from copy import deepcopy
import six
import os
from weblib import metric
from contextlib import contextmanager
from traceback import format_exc
import multiprocessing
import threading

from grab.base import Grab
from grab.error import GrabInvalidUrl
from grab.spider.error import (SpiderError, SpiderMisuseError, FatalError,
                               NoTaskHandler, NoDataHandler,
                               SpiderConfigurationError)
from grab.spider.task import Task
from grab.spider.data import Data
from grab.spider.transport.multicurl import MulticurlTransport
from grab.proxylist import ProxyList, BaseProxySource
from grab.util.misc import camel_case_to_underscore
from weblib.encoding import make_str, make_unicode
from grab.base import GLOBAL_STATE
from grab.stat import Stat, Timer

DEFAULT_TASK_PRIORITY = 100
DEFAULT_NETWORK_STREAM_NUMBER = 3
DEFAULT_TASK_TRY_LIMIT = 3
DEFAULT_NETWORK_TRY_LIMIT = 3
RANDOM_TASK_PRIORITY_RANGE = (50, 100)
NULL = object()

logger = logging.getLogger('grab.spider.base')
logger_verbose = logging.getLogger('grab.spider.base.verbose')
# If you need verbose logging just
# change logging level of that logger
logger_verbose.setLevel(logging.FATAL)


class SpiderMetaClass(type):
    """
    This meta class does following things::

    * It creates Meta attribute if it does not defined in
        Spider descendant class by copying parent's Meta attribute
    * It reset Meta.abstract to False if Meta is copied from parent class
    * If defined Meta does not contains `abstract`
        attribute then define it and set to False
    """

    def __new__(cls, name, bases, namespace):
        if 'Meta' not in namespace:
            for base in bases:
                if hasattr(base, 'Meta'):
                    # copy contents of base Meta
                    meta = type('Meta', (object,), dict(base.Meta.__dict__))
                    # reset abstract attribute
                    meta.abstract = False
                    namespace['Meta'] = meta
                    break

        # Process special case (SpiderMetaClassMixin)
        if 'Meta' not in namespace:
            namespace['Meta'] = type('Meta', (object,), {})

        if not hasattr(namespace['Meta'], 'abstract'):
            namespace['Meta'].abstract = False

        return super(SpiderMetaClass, cls).__new__(cls, name, bases, namespace)


@six.add_metaclass(SpiderMetaClass)
class Spider(object):
    """
    Asynchronous scraping framework.
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

    class Meta:
        # Meta.abstract means that this class will not be
        # collected to spider registry by `grab crawl` CLI command.
        # The Meta is inherited by descendant classes BUT
        # Meta.abstract is reset to False in each descendant
        abstract = True

    # *************
    # Class Methods
    # *************

    @classmethod
    def setup_spider_config(cls, config):
        pass

    @classmethod
    def get_spider_name(cls):
        if hasattr(cls, 'spider_name'):
            return cls.spider_name
        else:
            return camel_case_to_underscore(cls.__name__)

    # **************
    # Public Methods
    # **************

    def __init__(self, thread_number=None,
                 network_try_limit=None, task_try_limit=None,
                 request_pause=NULL,
                 priority_mode='random',
                 meta=None,
                 only_cache=False,
                 config=None,
                 slave=False,
                 max_task_generator_chunk=None,
                 args=None,
                 # New options start here
                 taskq=None,
                 # MP:
                 network_result_queue=None,
                 parser_result_queue=None,
                 waiting_shutdown_event=None,
                 shutdown_event=None,
                 mp_mode=False,
                 parser_pool_size=None,
                 parser_mode=False,
                 # http api
                 http_api_port=None,
                 ):
        """
        Arguments:
        * thread-number - Number of concurrent network streams
        * network_try_limit - How many times try to send request
            again if network error was occurred, use 0 to disable
        * network_try_limit - Limit of tries to execute some task
            this is not the same as network_try_limit
            network try limit limits the number of tries which
            are performed automatically in case of network timeout
            of some other physical error
            but task_try_limit limits the number of attempts which
            are scheduled manually in the spider business logic
        * priority_mode - could be "random" or "const"
        * meta - arbitrary user data
        * retry_rebuild_user_agent - generate new random user-agent for each
            network request which is performed again due to network error
        * args - command line arguments parsed with `setup_arg_parser` method
        New options:
        * taskq=None,
        * newtork_response_queue=None,
        """

        if slave:
            raise SpiderConfigurtionError(
                'Slave mode is not supported anymore. '
                'Use multiprocess mode instead.')

        # API:
        self.http_api_port = http_api_port

        # MP:
        self.mp_mode = mp_mode
        if self.mp_mode:
            from multiprocessing import Process, Event, Queue
        else:
            from multiprocessing.dummy import Process, Event, Queue

        if network_result_queue is not None:
            self.network_result_queue = network_result_queue
        else:
            self.network_result_queue = Queue()
        self.parser_result_queue = parser_result_queue
        self.waiting_shutdown_event = waiting_shutdown_event
        if shutdown_event is not None:
            self.shutdown_event = shutdown_event
        else:
            self.shutdown_event = Event()
        if not self.mp_mode and parser_pool_size and parser_pool_size > 1:
            raise SpiderConfigurationError(
                'Parser pool size could be only 1 in '
                'non-multiprocess mode')
        self.parser_pool_size = parser_pool_size
        self.parser_mode = parser_mode

        self.stat = Stat()
        self.timer = Timer()
        self.task_queue = taskq

        if args is None:
            self.args = {}
        else:
            self.args = args


        self.max_task_generator_chunk = max_task_generator_chunk
        self.timer.start('total')
        if config is not None:
            self.config = config
        else:
            self.config = {}

        if meta:
            self.meta = meta
        else:
            self.meta = {}

        self.task_generator_enabled = False
        self.only_cache = only_cache

        self.thread_number = (
            thread_number or
            int(self.config.get('thread_number',
                                DEFAULT_NETWORK_STREAM_NUMBER)))
        self.task_try_limit = (
            task_try_limit or
            int(self.config.get('task_try_limit', DEFAULT_TASK_TRY_LIMIT)))
        self.network_try_limit = (
            network_try_limit or
            int(self.config.get('network_try_limit',
                                DEFAULT_NETWORK_TRY_LIMIT)))

        self._grab_config = {}
        if priority_mode not in ['random', 'const']:
            raise SpiderMisuseError('Value of priority_mode option should be '
                                    '"random" or "const"')
        else:
            self.priority_mode = priority_mode

        # Initial cache-subsystem values
        self.cache_enabled = False
        self.cache = None

        self.work_allowed = True
        if request_pause is not NULL:
            logger.error('Option `request_pause` is deprecated and is not '
                         'supported anymore')

        self.proxylist_enabled = None
        self.proxylist = None
        self.proxy = None
        self.proxy_auto_change = False
        self.interrupted = False

    def setup_cache(self, backend='mongo', database=None, use_compression=True,
                    **kwargs):
        if database is None:
            raise SpiderMisuseError('setup_cache method requires database '
                                    'option')
        self.cache_enabled = True
        mod = __import__('grab.spider.cache_backend.%s' % backend,
                         globals(), locals(), ['foo'])
        self.cache = mod.CacheBackend(database=database,
                                      use_compression=use_compression,
                                      spider=self, **kwargs)

    def setup_queue(self, backend='memory', **kwargs):
        logger.debug('Using %s backend for task queue' % backend)
        mod = __import__('grab.spider.queue_backend.%s' % backend,
                         globals(), locals(), ['foo'])
        self.task_queue = mod.QueueBackend(spider_name=self.get_spider_name(),
                                           **kwargs)

    def add_task(self, task, raise_error=False):
        """
        Add task to the task queue.
        """

        # MP:
        # ***
        if self.parser_mode:
            self.parser_result_queue.put(task)
            return

        if self.task_queue is None:
            raise SpiderMisuseError('You should configure task queue before '
                                    'adding tasks. Use `setup_queue` method.')
        if task.priority is None or not task.priority_is_custom:
            task.priority = self.generate_task_priority()
            task.priority_is_custom = False
        else:
            task.priority_is_custom = True

        try:
            if not task.url.startswith(('http://', 'https://', 'ftp://',
                                        'file://', 'feed://')):
                if self.base_url is None:
                    msg = 'Could not resolve relative URL because base_url ' \
                          'is not specified. Task: %s, URL: %s'\
                          % (task.name, task.url)
                    raise SpiderError(msg)
                else:
                    task.url = urljoin(self.base_url, task.url)
                    # If task has grab_config object then update it too
                    if task.grab_config:
                        task.grab_config['url'] = task.url
        except Exception as ex:
            self.stat.collect('task-with-invalid-url', task.url)
            if raise_error:
                raise
            else:
                logger.error('', exc_info=ex)
                return False

        # TODO: keep original task priority if it was set explicitly
        self.task_queue.put(task, task.priority, schedule_time=task.schedule_time)
        return True

    def stop(self):
        """
        This method set internal flag which signal spider
        to stop processing new task and shuts down.
        """

        logger_verbose.debug('Method `stop` was called')
        self.work_allowed = False

    def load_proxylist(self, source, source_type=None, proxy_type='http',
                       auto_init=True, auto_change=True,
                       **kwargs):
        self.proxylist = ProxyList()
        if isinstance(source, BaseProxySource):
            self.proxylist.set_source(source)
        elif isinstance(source, six.string_types):
            if source_type == 'text_file':
                self.proxylist.load_file(source, proxy_type=proxy_type)
            elif source_type == 'url':
                self.proxylist.load_url(source, proxy_type=proxy_type)
            else:
                raise SpiderMisuseError('Method `load_proxylist` received '
                                        'invalid `source_type` argument: %s'
                                        % source_type) 
        else:
            raise SpiderMisuseError('Method `load_proxylist` received '
                                    'invalid `source` argument: %s'
                                    % source) 

        self.proxylist_enabled = True
        self.proxy = None
        if not auto_change and auto_init:
            self.proxy = self.proxylist.get_random_proxy()
        self.proxy_auto_change = auto_change

    def process_next_page(self, grab, task, xpath,
                          resolve_base=False, **kwargs):
        """
        Generate task for next page.

        :param grab: Grab instance
        :param task: Task object which should be assigned to next page url
        :param xpath: xpath expression which calculates list of URLS
        :param **kwargs: extra settings for new task object

        Example::

            self.follow_links(grab, 'topic', '//div[@class="topic"]/a/@href')
        """
        try:
            # next_url = grab.xpath_text(xpath)
            next_url = grab.doc.select(xpath).text()
        except IndexError:
            return False
        else:
            url = grab.make_url_absolute(next_url, resolve_base=resolve_base)
            page = task.get('page', 1) + 1
            grab2 = grab.clone()
            grab2.setup(url=url)
            task2 = task.clone(task_try_count=1, grab=grab2,
                               page=page, **kwargs)
            self.add_task(task2)
            return True

    def render_stats(self, timing=True):
        out = ['------------ Stats: ------------']
        out.append('Counters:')

        # Process counters
        items = sorted(self.stat.counters.items(),
                       key=lambda x: x[0], reverse=True)
        for item in items:
            out.append('  %s: %s' % item)
        out.append('')

        out.append('Lists:')
        # Process collections sorted by size desc
        col_sizes = [(x, len(y)) for x, y in self.stat.collections.items()]
        col_sizes = sorted(col_sizes, key=lambda x: x[1], reverse=True)
        for col_size in col_sizes:
            out.append('  %s: %d' % col_size)
        out.append('')

        # Process extra metrics
        if 'download-size' in self.stat.counters:
            out.append('Network download: %s' %
                       metric.format_traffic_value(
                           self.stat.counters['download-size']))
        out.append('Queue size: %d' % self.task_queue.size()
                                      if self.task_queue else 'NA')
        out.append('Network streams: %d' % self.thread_number)

        if timing:
            out.append('')
            out.append(self.render_timing())
        return '\n'.join(out) + '\n'

    def render_timing(self):
        out = ['Timers:']
        out.append('  DOM: %.3f' % GLOBAL_STATE['dom_build_time'])
        time_items = [(x, y) for x, y in self.timer.timers.items()]
        time_items = sorted(time_items, key=lambda x: x[1])
        for time_item in time_items:
            out.append('  %s: %.03f' % time_item)
        return '\n'.join(out) + '\n'

    # ********************************
    # Methods for spider customization
    # ********************************

    def prepare(self):
        """
        You can do additional spider customization here
        before it has started working. Simply redefine
        this method in your Spider class.
        """


    def prepare_parser(self):
        """
        You can do additional spider customization here
        before it has started working. Simply redefine
        this method in your Spider class.

        This method is called only from Spider working in parser mode
        that, in turn, is spawned automatically by main spider proces
        working in multiprocess mode.
        """

    def shutdown(self):
        """
        You can override this method to do some final actions
        after parsing has been done.
        """

        pass

    def update_grab_instance(self, grab):
        """
        Use this method to automatically update config of any
        `Grab` instance created by the spider.
        """
        pass

    def create_grab_instance(self, **kwargs):
        # Back-ward compatibility for deprecated `grab_config` attribute
        # Here I use `_grab_config` to not trigger warning messages
        if self._grab_config and kwargs:
            merged_config = deepcopy(self._grab_config)
            merged_config.update(kwargs)
            grab = Grab(**merged_config)
        elif self._grab_config and not kwargs:
            grab = Grab(**self._grab_config)
        else:
            grab = Grab(**kwargs)
        return grab

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

    # ***************
    # Private Methods
    # ***************

    def check_task_limits(self, task):
        """
        Check that task's network & try counters do not exceed limits.

        Returns:
        * if success: (True, None)
        * if error: (False, reason)

        """

        if task.task_try_count > self.task_try_limit:
            logger.debug('Task tries (%d) ended: %s / %s' % (
                          self.task_try_limit, task.name, task.url))
            return False, 'task-try-count'

        if task.network_try_count > self.network_try_limit:
            logger.debug('Network tries (%d) ended: %s / %s' % (
                          self.network_try_limit, task.name, task.url))
            return False, 'network-try-count'

        return True, None

    def generate_task_priority(self):
        if self.priority_mode == 'const':
            return DEFAULT_TASK_PRIORITY
        else:
            return randint(*RANDOM_TASK_PRIORITY_RANGE)

    def process_task_generator(self):
        """
        Load new tasks from `self.task_generator_object`
        Create new tasks.

        If task queue size is less than some value
        then load new tasks from tasks file.
        """

        if self.task_generator_enabled:
            queue_size = self.task_queue.size()
            if self.max_task_generator_chunk is not None:
                min_limit = min(self.max_task_generator_chunk,
                                self.thread_number * 10)
            else:
                min_limit = self.thread_number * 10
            if queue_size < min_limit:
                logger_verbose.debug(
                    'Task queue contains less tasks (%d) than '
                    'allowed limit (%d). Trying to add '
                    'new tasks.' % (queue_size, min_limit))
                try:
                    for x in six.moves.range(min_limit - queue_size):
                        item = next(self.task_generator_object)
                        logger_verbose.debug('Got new item from generator. '
                                             'Processing it.')
                        self.process_handler_result(item)
                except StopIteration:
                    # If generator have no values to yield
                    # then disable it
                    logger_verbose.debug('Task generator has no more tasks. '
                                         'Disabling it')
                    self.task_generator_enabled = False

    def start_task_generator(self):
        """
        Process `self.initial_urls` list and `self.task_generator`
        method.  Generate first portion of tasks.
        """

        logger_verbose.debug('Processing initial urls')
        if self.initial_urls:
            for url in self.initial_urls:
                self.add_task(Task('initial', url=url))

        self.task_generator_object = self.task_generator()
        self.task_generator_enabled = True
        # Initial call to task generator before spider has started working
        self.process_task_generator()

    def get_task_from_queue(self):
        start = time.time()
        try:
            with self.timer.log_time('task_queue'):
                return self.task_queue.get()
        except queue.Empty:
            size = self.task_queue.size()
            if size:
                logger_verbose.debug(
                    'No ready-to-go tasks, Waiting for '
                    'scheduled tasks (%d)' % size)
                return True
            else:
                logger_verbose.debug('Task queue is empty.')
                return None

    def setup_grab_for_task(self, task):
        grab = self.create_grab_instance()
        if task.grab_config:
            grab.load_config(task.grab_config)
        else:
            grab.setup(url=task.url)

        # Generate new common headers
        grab.config['common_headers'] = grab.common_headers()
        self.update_grab_instance(grab)
        return grab

    def is_task_cacheable(self, task, grab):
        if (    # cache is disabled for all tasks
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

    def load_task_from_cache(self, task, grab, grab_config_backup):
        with self.timer.log_time('cache'):
            with self.timer.log_time('cache.read'):
                cache_item = self.cache.get_item(
                    grab.config['url'], timeout=task.cache_timeout)
                if cache_item is None:
                    return None
                else:
                    with self.timer.log_time('cache.read.prepare_request'):
                        grab.prepare_request()
                    with self.timer.log_time('cache.read.load_response'):
                        self.cache.load_response(grab, cache_item)

                    grab.log_request('CACHED')
                    self.stat.inc('spider:request-cache')

                    return {'ok': True, 'grab': grab,
                            'grab_config_backup': grab_config_backup,
                            'task': task, 'emsg': None}

    def is_valid_network_response_code(self, code, task):
        """
        Answer the question: if the response could be handled via
        usual task handler or the task faield and should be processed as error.
        """

        return (code < 400 or code == 404 or
                code in task.valid_status)

    def process_handler_error(self, func_name, ex, task):
        self.stat.inc('spider:error-%s' % ex.__class__.__name__.lower())

        if hasattr(ex, 'tb'):
            logger.error('Error in %s function' % func_name)
            logger.error(ex.tb)
        else:
            logger.error('Error in %s function' % func_name, exc_info=ex)

        # Looks strange but I really have some problems with
        # serializing exception into string
        try:
            ex_str = six.text_type(ex)
        except TypeError:
            try:
                ex_str = ex.decode('utf-8', 'ignore')
            except TypeError:
                ex_str = str(ex)

        task_url = task.url if task is not None else None
        self.stat.collect('fatal', '%s|%s|%s|%s' % (
            func_name, ex.__class__.__name__, ex_str, task_url))
        if isinstance(ex, FatalError):
            #raise FatalError()
            #six.reraise(FatalError, ex)
            #logger.error(ex.tb)
            raise ex

    def find_data_handler(self, data):
        try:
            return getattr(data, 'handler')
        except AttributeError:
            try:
                handler = getattr(self, 'data_%s' % data.handler_key)
            except AttributeError:
                raise NoDataHandler('No handler defined for Data %s'
                                    % data.handler_key)
            else:
                return handler

    def is_valid_network_result(self, res):
        if res['task'].get('raw'):
            return True
        if res['ok']:
            res_code = res['grab'].response.code
            if self.is_valid_network_response_code(res_code, res['task']):
                return True
        return False

    def run_parser(self):
        """
        Main work cycle of spider process working in parser-mode.
        """
        # Use Stat instance that does not print any logging messages
        if self.parser_mode:
            self.stat = Stat(logging_period=None)
        self.prepare_parser()
        try:
            recent_task_time = time.time()
            while True:
                try:
                    result = self.network_result_queue.get(True, 0.1)
                except queue.Empty:
                    logger_verbose.debug('Network result queue is empty')
                    # Set `waiting_shutdown_event` only after 1 seconds
                    # of waiting for tasks to avoid
                    # race-condition issues
                    if time.time() - recent_task_time > 1:
                        self.waiting_shutdown_event.set()
                    if self.shutdown_event.is_set():
                        logger_verbose.debug('Got shutdown event')
                        return
                else:
                    recent_task_time = time.time()
                    if self.parser_mode:
                        self.stat.reset()
                    if self.waiting_shutdown_event.is_set():
                        self.waiting_shutdown_event.clear()
                    try:
                        handler = self.find_task_handler(result['task'])
                    except NoTaskHandler as ex:
                        ex.tb = format_exc()
                        self.parser_result_queue.put((ex, result['task']))
                        self.stat.inc('parser:handler-not-found')
                    else:
                        self.process_network_result_with_handler_mp(
                            result, handler)
                        self.stat.inc('parser:handler-processed')
                    finally:
                        if self.parser_mode:
                            data = {
                                'type': 'stat',
                                'counters': self.stat.counters,
                                'collections': self.stat.collections,
                            }
                            self.parser_result_queue.put((data, result['task']))
        except Exception as ex:
            logging.error('', exc_info=ex)
            raise
        finally:
            self.waiting_shutdown_event.set()


    def process_network_result_with_handler_mp(self, result, handler):
        """
        This is like `process_network_result_with_handler` but
        for multiprocessing version
        """
        handler_name = getattr(handler, '__name__', 'NONE')
        try:
            with self.timer.log_time('response_handler'):
                with self.timer.log_time('response_handler.%s' % handler_name):
                    handler_result = handler(result['grab'], result['task'])
                    if handler_result is None:
                        pass
                    else:
                        for something in handler_result:
                            self.parser_result_queue.put((something,
                                                          result['task']))
        except NoDataHandler as ex:
            ex.tb = format_exc()
            self.parser_result_queue.put((ex, result['task']))
        except Exception as ex:
            ex.tb = format_exc()
            self.parser_result_queue.put((ex, result['task']))

    def find_task_handler(self, task):
        if task.origin_task_generator is not None:
            return self.handler_for_inline_task
        callback = task.get('callback')
        if callback:
            return callback
        else:
            try:
                handler = getattr(self, 'task_%s' % task.name)
            except AttributeError:
                raise NoTaskHandler('No handler or callback defined for '
                                    'task %s' % task.name)
            else:
                return handler

    def handler_for_inline_task(self, grab, task):
        # It can be subroutine for the first call,
        # So we should check it
        if isinstance(task, types.GeneratorType):
            coroutines_stack = []
            sendval = None
            origin_task_generator = task
            target = origin_task_generator
        else:
            coroutines_stack = task.coroutines_stack
            sendval = grab
            origin_task_generator = task.origin_task_generator
            target = origin_task_generator

        while True:
            try:
                result = target.send(sendval)
                # If it is subroutine we have to initialize it and
                # save coroutine in the coroutines stack
                if isinstance(result, types.GeneratorType):
                    coroutines_stack.append(target)
                    sendval = None
                    target = result
                    origin_task_generator = target
                else:
                    new_task = result
                    new_task.origin_task_generator = origin_task_generator
                    new_task.coroutines_stack = coroutines_stack
                    self.add_task(new_task)
                    return
            except StopIteration:
                # If coroutine is over we should check coroutines stack,
                # may be it is subroutine
                if coroutines_stack:
                    target = coroutines_stack.pop()
                    origin_task_generator = target
                else:
                    return

    def log_network_result_stats(self, res, from_cache=False):
        # Increase stat counters
        self.stat.inc('spider:request-processed')
        self.stat.inc('spider:task')
        self.stat.inc('spider:task-%s' % res['task'].name)
        if (res['task'].network_try_count == 1 and
                res['task'].task_try_count == 1):
            self.stat.inc('spider:task-%s-initial' % res['task'].name)

        # Update traffic statistics
        if res['grab'] and res['grab'].response:
            resp = res['grab'].response
            self.timer.inc_timer('network-name-lookup', resp.name_lookup_time)
            self.timer.inc_timer('network-connect', resp.connect_time)
            self.timer.inc_timer('network-total', resp.total_time)
            if from_cache:
                self.stat.inc('spider:download-size-with-cache',
                              resp.download_size)
                self.stat.inc('spider:upload-size-with-cache',
                              resp.upload_size)
            else:
                self.stat.inc('spider:download-size', resp.download_size)
                self.stat.inc('spider:upload-size', resp.upload_size)


    def process_grab_proxy(self, task, grab):
        "Assign new proxy from proxylist to the task"

        if task.use_proxylist:
            if self.proxylist_enabled:
                if self.proxy_auto_change:
                    self.proxy = self.change_proxy(task, grab)

    def change_proxy(self, task, grab):
        proxy = self.proxylist.get_random_proxy()
        grab.setup(proxy=proxy.get_address(),
                   proxy_userpwd=proxy.get_userpwd(),
                   proxy_type=proxy.proxy_type)
        return proxy

    def submit_task_to_transport(self, task, grab, grab_config_backup):
        self.stat.inc('spider:request-network')
        self.stat.inc('spider:task-%s-network' % task.name)
        self.process_grab_proxy(task, grab)
        with self.timer.log_time('network_transport'):
            logger_verbose.debug('Submitting task to the transport '
                                 'layer')
            try:
                self.transport.start_task_processing(
                    task, grab, grab_config_backup)
            except GrabInvalidUrl:
                logger.debug('Task %s has invalid URL: %s' % (
                    task.name, task.url))
                self.stat.collect('invalid-url', task.url)

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
                        if self.is_valid_network_response_code(
                                res['grab'].response.code, res['task']):
                            return True
        return False

    def start_api_thread(self):
        from grab.spider.http_api import HttpApiThread

        proc = HttpApiThread(self)
        proc.start()
        return proc

    def run(self):
        """
        Main method. All work is done here.
        """
        if self.mp_mode:
            from multiprocessing import Process, Event, Queue
        else:
            from multiprocessing.dummy import Process, Event, Queue

        self.timer.start('total')
        self.transport = MulticurlTransport(self.thread_number)

        if self.http_api_port:
            http_api_proc = self.start_api_thread()
        else:
            http_api_proc = None

        from grab.spider.parser_pipeline import ParserPipeline

        self.parser_pipeline = ParserPipeline(
            bot=self,
            mp_mode=self.mp_mode,
            pool_size=self.parser_pool_size,
            shutdown_event=self.shutdown_event,
            network_result_queue=self.network_result_queue)
        network_result_queue_limit = max(10, self.thread_number * 2)
        
        try:
            # Run custom things defined by this specific spider
            # By defaut it does nothing
            self.prepare()

            # Setup task queue if it has not been configured yet
            if self.task_queue is None:
                self.setup_queue()

            # Initiate task generator. Only in main process!
            with self.timer.log_time('task_generator'):
                self.start_task_generator()

            while self.work_allowed:
                with self.timer.log_time('task_generator'):
                    if self.task_generator_enabled:
                        self.process_task_generator()

                result_from_cache = None
                free_threads = self.transport.get_free_threads_number()
                # Load new task only if self.network_result_queue is not full
                if (self.transport.get_free_threads_number()
                        and (self.network_result_queue.qsize()
                             < network_result_queue_limit)):
                    logger_verbose.debug(
                        'Transport and parser have free resources. '
                        'Trying to load new task from task queue.')

                    task = self.get_task_from_queue()

                    if task is None:
                        if not self.transport.get_active_threads_number():
                            self.process_task_generator()

                    if task is None:
                        if (not self.transport.get_active_threads_number()
                                and not self.network_result_queue.qsize()
                                and not self.parser_pipeline.parser_result_queue.qsize()
                                and not self.task_queue.size()
                                and all([x['waiting_shutdown_event'].is_set()
                                         for x in self.parser_pipeline.parser_pool])):
                            logger_verbose.debug('Network transport has no '
                                                 'active tasks. No parser '
                                                 'futures. No pending results')
                            if not self.task_generator_enabled:
                                self.shutdown_event.set()
                                self.stop()
                        else:
                            logger_verbose.debug(
                                'Transport active tasks: %d' %
                                self.transport.get_active_threads_number())
                    elif isinstance(task, bool) and (task is True):
                        # Take some sleep to not load CPU
                        if not self.transport.get_active_threads_number():
                            time.sleep(0.1)
                    else:
                        logger_verbose.debug('Got new task from task queue: %s'
                                             % task)
                        task.network_try_count += 1
                        is_valid, reason = self.check_task_limits(task)
                        if is_valid:
                            grab = self.setup_grab_for_task(task)
                            grab_config_backup = grab.dump_config()

                            result_from_cache = None
                            if self.is_task_cacheable(task, grab):
                                result_from_cache = self.load_task_from_cache(
                                    task, grab, grab_config_backup)

                            if result_from_cache:
                                logger_verbose.debug(
                                    'Task data is loaded from the cache. ')
                            else:
                                if self.only_cache:
                                    logger.debug('Skipping network request to '
                                                 '%s' % grab.config['url'])
                                else:
                                    self.submit_task_to_transport(
                                        task, grab, grab_config_backup)
                        else:
                            self.log_rejected_task(task, reason)
                            handler = task.get_fallback_handler(self)
                            if handler:
                                handler(task)

                with self.timer.log_time('network_transport'):
                    logger_verbose.debug('Asking transport layer to do '
                                         'something')
                    self.transport.process_handlers()

                logger_verbose.debug('Processing network results (if any).')

                # Collect completed network results
                # Each result could be valid or failed
                # Result is dict {ok, grab, grab_config_backup, task, emsg}
                results = [(x, False) for x in
                           self.transport.iterate_results()]
                if result_from_cache:
                    results.append((result_from_cache, True))

                # Some sleep to avoid thousands of iterations per second.
                # If no results from network transport
                if not results:
                    # If task queue is empty (or if there are only
                    # delayed tasks)
                    if task is None or bool(task) == True:
                        # If no network activity
                        if not self.transport.get_active_threads_number():
                            # If parser (hander result) queue is empty
                            if not self.parser_pipeline.parser_result_queue.qsize():
                                # Just sleep some time, do not kill CPU
                                time.sleep(0.1)

                for result, from_cache in results:
                    if not from_cache:
                        if self.is_valid_for_cache(result):
                            with self.timer.log_time('cache'):
                                with self.timer.log_time('cache.write'):
                                    self.cache.save_response(
                                        result['task'].url, result['grab'])
                    self.log_network_result_stats(
                        result, from_cache=from_cache)
                    if self.is_valid_network_result(result):
                        #handler = self.find_task_handler(result['task'])
                        #self.process_network_result_with_handler(
                        #    result, handler)
                        # MP:
                        # ***
                        self.network_result_queue.put(result)
                    else:
                        self.log_failed_network_result(result)
                        # Try to do network request one more time
                        if self.network_try_limit > 0:
                            result['task'].refresh_cache = True
                            result['task'].setup_grab_config(
                                result['grab_config_backup'])
                            self.add_task(result['task'])
                    if from_cache:
                        self.stat.inc('spider:task-%s-cache' % task.name)
                    self.stat.inc('spider:request')

                # MP:
                # ***
                while True:
                    try:
                        p_res, p_task = self.parser_pipeline\
                                            .parser_result_queue.get_nowait()
                    except queue.Empty:
                        break
                    else:
                        self.stat.inc('spider:parser-result')
                        self.process_handler_result(p_res, p_task)

                if not self.shutdown_event.is_set():
                    self.parser_pipeline.check_pool_health()

            logger_verbose.debug('Work done')
        except KeyboardInterrupt:
            logger.info('\nGot ^C signal in process %d. Stopping.'
                        % os.getpid())
            self.interrupted = True
            raise
        finally:
            # This code is executed when main cycles is breaked
            self.timer.stop('total')
            self.stat.print_progress_line()
            self.shutdown()

            # Stop HTTP API process
            if http_api_proc:
                http_api_proc.server.shutdown()
                http_api_proc.join()

            # Stop parser processes
            self.shutdown_event.set()
            self.parser_pipeline.shutdown()
            logger.debug('Main process [pid=%s]: work done' % os.getpid())

    def log_failed_network_result(self, res):
        # Log the error
        if res['ok']:
            msg = 'http-%s' % res['grab'].response.code
        else:
            msg = res['error_abbr']

        self.stat.inc('error:%s' % msg) 
        #logger.error(u'Network error: %s' % msg)#%
                     #make_unicode(msg, errors='ignore'))

    def log_rejected_task(self, task, reason):
        logger_verbose.debug('Task %s is rejected due to '
                             '%s limit'
                             % (task.name, reason))
        if reason == 'task-try-count':
            self.stat.collect('task-count-rejected',
                             task.url)
        elif reason == 'network-try-count':
            self.stat.collect('network-count-rejected',
                             task.url)
        else:
            raise SpiderError('Unknown response from '
                              'check_task_limits: %s'
                              % reason)

    def process_handler_result(self, result, task=None):
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
            handler = self.find_data_handler(result)
            try:
                data_result = handler(**result.storage)
                if data_result is None:
                    pass
                else:
                    for something in data_result:
                        self.process_handler_result(something, task)

            except Exception as ex:
                self.process_handler_error('data_%s' % result.handler_key, ex,
                                           task)
        elif result is None:
            pass
        elif isinstance(result, Exception): 
            handler = self.find_task_handler(task)
            handler_name = getattr(handler, '__name__', 'NONE')
            self.process_handler_error(handler_name, result, task)
        elif isinstance(result, dict):
            if result.get('type') == 'stat':
                for name, count in result['counters'].items():
                    self.stat.inc(name, count)
                for name, items in result['collections'].items():
                    for item in items:
                        self.stat.collect(name, item)
            else:
                raise SpiderError('Unknown result type: %s' % result)
        else:
            raise SpiderError('Unknown result type: %s' % result)

    # ******************
    # Deprecated Methods
    # ******************

    def add_item(self, list_name, item):
        logger.debug('Method `Spider::add_item` is deprecated. '
                     'Use `Spider::stat.collect` method instead.')
        self.stat.collect(list_name, item)

    def inc_count(self, key, count=1):
        logger.debug('Method `Spider::inc_count` is deprecated. '
                     'Use `Spider::stat.inc` method instead.')
        self.stat.inc(key, count)

    def start_timer(self, key):
        logger.debug('Method `Spider::start_timer` is deprecated. '
                     'Use `Spider::timer.start` method instead.')
        self.timer.start(key)

    def stop_timer(self, key):
        logger.debug('Method `Spider::stop_timer` is deprecated. '
                     'Use `Spider::timer.stop` method instead.')
        self.timer.stop(key)

    @property
    def items(self):
        logger.debug('Attribute `Spider::items` is deprecated. '
                     'Use `Spider::stat.collections` attribute instead.')
        return self.stat.collections

    @property
    def counters(self):
        logger.debug('Attribute `Spider::counters` is deprecated. '
                     'Use `Spider::stat.counters` attribute instead.')
        return self.stat.counters

    @contextmanager
    def save_timer(self, key):
        logger.debug('Method `Spider::save_timer` is deprecated. '
                     'Use `Spider::timer.log_time` method instead.')
        self.timer.start(key)
        try:
            yield
        finally:
            self.timer.stop(key)

    def get_grab_config(self):
        logger.error('Using `grab_config` attribute is deprecated. Override '
                     '`create_grab_instance method instead.')
        return self._grab_config

    def set_grab_config(self, val):
        logger.error('Using `grab_config` attribute is deprecated. Override '
                     '`create_grab_instance method instead.')
        self._grab_config = val

    grab_config = property(get_grab_config, set_grab_config)

    def setup_grab(self, **kwargs):
        logger.error('Method `Spider::setup_grab` is deprecated. '
                     'Define `Spider::create_grab_instance` or '
                     'Spider::update_grab_instance` methods in your '
                     'Spider sub-class.')
        self.grab_config.update(**kwargs)

    def valid_response_code(self, code, task):
        logger.error('Method `Spider::valid_response_code` is deprecated. '
                     'Use `Spider::is_valid_network_response_code` method or '
                     '`Spider::is_valid_network_result` method.')
        return self.is_valid_network_response_code(code, task)

    @property
    def taskq(self):
        logger.error('Attribute `Spider::taskq` is deprecated. '
                     'Use `Spider::task_queue` attribute.')
        return self.task_queue
