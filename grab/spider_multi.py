1/0
from Queue import PriorityQueue, Empty
import pycurl
from grab import Grab
import logging
import types
from collections import defaultdict
import os
import time
import signal
import json
import cPickle as pickle
#from guppy import hpy
#hp = hpy()
#hp.setrelheap()
import anydbm
import multiprocessing
from Queue import Empty
from lxml.html import fromstring

def execute_handler(handler, handler_name, res_count, queue,
                    grab, task):
    try:
        res = handler(grab, task)
        queue.put((res_count, handler_name, res))
    except Exception, ex:
        return {'error': ex}

from spider import SpiderError, SpiderMisuseError, Task, Data

class Spider(object):
    """
    Asynchronious scraping framework.
    """

    # You can define here some urls and initial tasks
    # with name "initial" will be created from these
    # urls
    initial_urls = None

    def __init__(self, thread_number=3, request_limit=None,
                 network_try_limit=10, task_try_limit=10,
                 debug_error=False, use_cache=False,
                 cache_db = None,
                 cache_path='var/cache.db',
                 log_taskname=False,
                 use_pympler=False,
                 module=None):
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
        """

        self.taskq = PriorityQueue()
        self.thread_number = thread_number
        self.request_limit = request_limit
        self.counters = defaultdict(int)
        self.grab_config = {}
        self.proxylist_config = None
        self.items = {}
        self.task_try_limit = task_try_limit
        self.network_try_limit = network_try_limit
        self.task_generator_object = self.task_generator()
        self.task_generator_enabled = True
        self.process_task_generator()
        try:
            signal.signal(signal.SIGUSR1, self.sigusr1_handler)
        except AttributeError:
            pass
        self.debug_error = debug_error
        self.use_cache = use_cache
        #self.mongo_dbname = mongo_dbname
        self.cache_path = cache_path
        self.cache_db = cache_db
        if use_cache:
            self.setup_cache()
        self.log_taskname = log_taskname
        self.prepare()
        self.module = module

        #if self.use_pympler:
            #from pympler import tracker
            #self.tracker = tracker.SummaryTracker()
            #self.tracker.print_diff()

    def setup_cache(self):
        import pymongo
        if not self.cache_db:
            raise Exception('You should configure cache_db option')
        self.cache = pymongo.Connection()[self.cache_db]['cache']
        #from tcdb import hdb 
        #import tc
        #self.cache = hdb.HDB()
        #self.cache = tc.HDB()
        #self.cache.open(self.cache_path, tc.HDBOWRITER | tc.HDBOCREAT | tc.HDBOTRUNC)
        #self.cache = anydbm.open(self.cache_path, 'c')

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


    def load_tasks(self, path, task_name='initial', task_priority=100,
                   limit=None):
        count = 0
        with open(path) as inf:
            for line in inf:
                url = line.strip()
                if url:
                    self.taskq.put((task_priority, Task(task_name, url)))
                    count += 1
                    if limit is not None and count >= limit:
                        logging.debug('load_tasks limit reached')
                        break

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

    def run(self):
        self.start_time = time.time()
        self.load_initial_urls()

        # new
        pool = multiprocessing.Pool(1)
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        mapping = {}
        multi_requests = []

        for res_count, res in enumerate(self.fetch()):
            if res is None:
                break

            if self.task_generator_enabled:
                self.process_task_generator()

            # Increase task counters
            self.inc_count('task')
            self.inc_count('task-%s' % res['task'].name)
            if (res['task'].network_try_count == 1 and
                res['task'].task_try_count == 1):
                self.inc_count('task-%s-initial' % res['task'].name)
            if self.log_taskname:
                logging.debug('TASK: %s - %s' % (res['task'].name,
                                                 'OK' if res['ok'] else 'FAIL'))

            handler_name = 'task_%s' % res['task'].name
            try:
                handler = getattr(self.module, handler_name)
            except AttributeError:
                raise Exception('Task handler does not exist: %s' %\
                                handler_name)
            else:
                # new

                if res['ok'] and (res['grab'].response.code < 400 or
                                  res['grab'].response.code == 404):
                    mapping[res_count] = res
                    res['grab'].curl = None
                    res['grab_original'].curl = None
                    multi_request = pool.apply_async(
                        execute_handler, (handler, handler_name, res_count,
                                          queue, res['grab'], res['task']))
                    multi_requests.append(multi_request)
                else:
                    # Log the error
                    if res['ok']:
                        res['emsg'] = 'HTTP %s' % res['grab'].response.code
                    self.inc_count('network-error-%s' % res['emsg'][:20])
                    logging.error(res['emsg'])

                    # Try to repeat the same network query
                    if self.network_try_limit > 0:
                        task = res['task']
                        task.grab = res['grab_original']
                        self.add_task(task)
                    # TODO: allow to write error handlers


                #self.execute_response_handler(res, handler, handler_name)

            try:
                res_count, handler_name, task_result = queue.get(False)
            except Empty:
                pass
            else:
                res = mapping[res_count]
                if isinstance(task_result, dict) and 'error' in task_result:
                    self.error_handler(handler_name, task_result['error'],
                                       res['task'])
                else:
                    self.process_result(task_result, res['task'])
                #import pdb; pdb.set_trace()
                #res['grab']._lxml_tree = tree
                #print tree.xpath('//h1')
                #self.execute_response_handler(res, handler, handler_name)
                del mapping[res_count]
            multi_requests = [x for x in multi_requests if not x.ready()]

        # new
        #while True:
            #try:
                #res_count, tree = queue.get(True, 0.1)
            #except Empty:
                #multi_requests = [x for x in multi_requests if not x.ready()]
                #if not len(multi_requests):
                    #break
            #else:
                #res = mapping[res_count]
                ##res['grab']._lxml_tree = tree
                #self.execute_response_handler(res, handler, handler_name)
                #del mapping[res_count]


        # This code is executed when main cycles is breaked
        self.shutdown()

    def execute_response_handler(self, res, handler, handler_name):
        if res['ok'] and (res['grab'].response.code < 400 or
                          res['grab'].response.code == 404):
            try:
                result = handler(res['grab'], res['task'])
                if isinstance(result, types.GeneratorType):
                    for item in result:
                        self.process_result(item, res['task'])
                else:
                    self.process_result(result, res['task'])
            except Exception, ex:
                self.error_handler(handler_name, ex, res['task'])
        else:
            # Log the error
            if res['ok']:
                res['emsg'] = 'HTTP %s' % res['grab'].response.code
            self.inc_count('network-error-%s' % res['emsg'][:20])
            logging.error(res['emsg'])

            # Try to repeat the same network query
            if self.network_try_limit > 0:
                task = res['task']
                task.grab = res['grab_original']
                self.add_task(task)
            # TODO: allow to write error handlers
    
    def process_result(self, result, task):
        """
        Process result returned from task handler. 
        Result could be None, Task instance or Data instance.
        """

        if isinstance(result, Task):
            if not self.add_task(result):
                self.add_item('wtf-error-task-not-added', task.url)
        elif isinstance(result, Data):
            handler_name = 'data_%s' % result.name
            try:
                handler = getattr(self, handler_name)
            except AttributeError:
                handler = self.data_default
            try:
                handler(result.item)
            except Exception, ex:
                self.error_handler(handler_name, ex, task)
        elif result is None:
            pass
        else:
            raise Exception('Unknown result type: %s' % result)

    def add_task(self, task):
        """
        Add new task to task queue.

        Stop the task which was executed too many times.
        """

        if task.task_try_count > self.task_try_limit:
            logging.debug('Task tries ended: %s / %s' % (task.name, task.url))
            return False
        elif task.network_try_count >= self.network_try_limit:
            logging.debug('Network tries ended: %s / %s' % (task.name, task.url))
            return False
        else:
            self.taskq.put((task.priority, task))
            return True

    def data_default(self, item):
        """
        Default handler for Content result for which
        no handler defined.
        """

        raise Exception('No content handler for %s item', item)

    def fetch(self):
        """
        Download urls via multicurl.
        
        Get new tasks from queue.
        """ 
        m = pycurl.CurlMulti()
        m.handles = []

        # Create curl instances
        for x in xrange(self.thread_number):
            curl = pycurl.Curl()
            m.handles.append(curl)

        freelist = m.handles[:]

        # This is infinite cycle
        # You can break it only from outside code which
        # iterates over result of this method
        while True:

            cached_request = None

            while len(freelist):

                # Increase request counter
                if (self.request_limit is not None and
                    self.counters['request'] >= self.request_limit):
                    logging.debug('Request limit is reached: %s' %\
                                  self.request_limit)
                    if len(freelist) == self.thread_number:
                        yield None
                    else:
                        break
                else:
                    try:
                        priority, task = self.taskq.get(True, 0.1)
                    except Empty:
                        # If All handlers are free and no tasks in queue
                        # yield None signal
                        if len(freelist) == self.thread_number:
                            yield None
                        else:
                            break
                    else:
                        if not self._preprocess_task(task):
                            continue

                        task.network_try_count += 1
                        if task.task_try_count == 0:
                            task.task_try_count = 1

                        if task.task_try_count > self.task_try_limit:
                            logging.debug('Task tries ended: %s / %s' % (
                                          task.name, task.url))
                            self.add_item('too-many-task-tries', task.url)
                            continue
                        
                        if task.network_try_count > self.network_try_limit:
                            logging.debug('Network tries ended: %s / %s' % (
                                          task.name, task.url))
                            self.add_item('too-many-network-tries', task.url)
                            continue

                        #import pdb; pdb.set_trace()
                        if task.grab:
                            grab = task.grab
                        else:
                            # Set up curl instance via Grab interface
                            grab = Grab(**self.grab_config)
                            grab.setup(url=task.url)

                        if self.use_cache and not task.get('disable_cache'):
                            if grab.detect_request_method() == 'GET':
                                url = grab.config['url']
                                cache_item = self.cache.find_one({'_id': url})
                                if cache_item:
                                #if url in self.cache:
                                    #cache_item = pickle.loads(self.cache[url])
                                    #logging.debug('From cache: %s' % url)
                                    cached_request = (grab, grab.clone(),
                                                      task, cache_item)
                                    grab.prepare_request()
                                    self.inc_count('request-cache')

                                    # break from prepre-request cycle
                                    # and go to process-response code
                                    break

                        self.inc_count('request-network')
                        if self.proxylist_config:
                            args, kwargs = self.proxylist_config
                            grab.setup_proxylist(*args, **kwargs)

                        curl = freelist.pop()
                        curl.grab = grab
                        curl.grab.curl = curl
                        curl.grab_original = grab.clone()
                        curl.grab.prepare_request()
                        curl.task = task
                        # Add configured curl instance to multi-curl processor
                        m.add_handle(curl)


            # If there were done network requests
            if len(freelist) != self.thread_number:
                while True:
                    status, active_objects = m.perform()
                    if status != pycurl.E_CALL_MULTI_PERFORM:
                        break

            if cached_request:
                grab, grab_original, task, cache_item = cached_request
                url = task.url# or grab.config['url']
                grab.fake_response(cache_item['body'])

                def custom_prepare_response(g):
                    g.response.head = cache_item['head'].encode('utf-8')
                    g.response.body = cache_item['body'].encode('utf-8')
                    g.response.code = cache_item['response_code']
                    g.response.time = 0
                    g.response.url = cache_item['url']
                    g.response.parse('utf-8')
                    g.response.cookies = g.extract_cookies()

                grab.process_request_result(custom_prepare_response)

                yield {'ok': True, 'grab': grab, 'grab_original': grab_original,
                       'task': task, 'ecode': None, 'emsg': None}
                self.inc_count('request')

            while True:
                queued_messages, ok_list, fail_list = m.info_read()

                results = []
                for curl in ok_list:
                    results.append((True, curl, None, None))
                for curl, ecode, emsg in fail_list:
                    results.append((False, curl, ecode, emsg))

                for ok, curl, ecode, emsg in results:
                    res = self.process_multicurl_response(ok, curl,
                                                          ecode, emsg)
                    m.remove_handle(curl)
                    freelist.append(curl)
                    yield res
                    self.inc_count('request')

                if not queued_messages:
                    break

            m.select(0.5)

    def process_multicurl_response(self, ok, curl, ecode=None, emsg=None):
        """
        Process reponse returned from multicurl cycle.
        """

        task = curl.task
        # Note: curl.grab == task.grab if task.grab is not None
        grab = curl.grab
        grab_original = curl.grab_original

        url = task.url# or grab.config['url']
        grab.process_request_result()

        # Break links, free resources
        curl.grab.curl = None
        curl.grab = None
        curl.task = None

        if ok and self.use_cache and grab.request_method == 'GET' and not task.get('disable_cache'):
            if grab.response.code < 400 or grab.response.code == 404:
                item = {
                    '_id': task.url,
                    'url': task.url,
                    'body': grab.response.unicode_body().encode('utf-8'),
                    'head': grab.response.head,
                    'response_code': grab.response.code,
                    'cookies': grab.response.cookies,
                }
                try:
                    #self.mongo.cache.save(item, safe=True)
                    self.cache.save(item, safe=True)
                except Exception, ex:
                    if 'document too large' in unicode(ex):
                        pass
                    else:
                        import pdb; pdb.set_trace()

        return {'ok': ok, 'grab': grab, 'grab_original': grab_original,
                'task': task,
                'ecode': ecode, 'emsg': emsg}

    def shutdown(self):
        """
        You can override this method to do some final actions
        after parsing has been done.
        """

        logging.debug('Job done!')
        #self.tracker.stats.print_summary()

    def inc_count(self, key, display=False, count=1):
        """
        You can call multiply time this method in process of parsing.

        self.inc_count('regurl')
        self.inc_count('captcha')

        and after parsing you can acces to all saved values:

        print 'Total: %(total)s, captcha: %(captcha)s' % spider_obj.counters
        """

        self.counters[key] += count
        if display:
            logging.debug(key)
        return self.counters[key]

    def setup_proxylist(self, *args, **kwargs):
        """
        Save proxylist config which will be later passed to Grab
        constructor.
        """

        self.proxylist_config = (args, kwargs)

    def add_item(self, list_name, item, display=False):
        """
        You can call multiply time this method in process of parsing.

        self.add_item('foo', 4)
        self.add_item('foo', 'bar')

        and after parsing you can acces to all saved values:

        spider_instance.items['foo']
        """

        lst = self.items.setdefault(list_name, [])
        lst.append(item)
        if display:
            logging.debug(list_name)

    def save_list(self, list_name, path):
        """
        Save items from list to the file.
        """

        with open(path, 'w') as out:
            lines = []
            for item in self.items.get(list_name, []):
                if isinstance(item, basestring):
                    lines.append(item)
                else:
                    lines.append(json.dumps(item))
            out.write('\n'.join(lines))

    def render_stats(self):
        out = []
        out.append('Counters:')
        # Sort counters by its names
        items = sorted(self.counters.items(), key=lambda x: x[0], reverse=True)
        out.append('  %s' % '\n  '.join('%s: %s' % x for x in items))
        out.append('\nLists:')
        # Sort lists by number of items
        items = [(x, len(y)) for x, y in self.items.items()]
        items = sorted(items, key=lambda x: x[1], reverse=True)
        out.append('  %s' % '\n  '.join('%s: %s' % x for x in items))

        total_time = time.time() - self.start_time
        out.append('Queue size: %d' % self.taskq.qsize())
        out.append('Threads: %d' % self.thread_number)
        out.append('Time: %.2f sec' % total_time)
        return '\n'.join(out)

    def save_all_lists(self, dir_path):
        """
        Save each list into file in specified diretory.
        """

        for key, items in self.items.items():
            path = os.path.join(dir_path, '%s.txt' % key)
            self.save_list(key, path)

    def error_handler(self, func_name, ex, task):
        self.inc_count('error-%s' % ex.__class__.__name__.lower())
        self.add_item('fatal', '%s|%s|%s' % (ex.__class__.__name__,
                                             unicode(ex), task.url))
        logging.error('Error in %s function' % func_name,
                      exc_info=ex)
        if self.debug_error:
            #import sys, traceback,  pdb
            #type, value, tb = sys.exc_info()
            #traceback.print_exc()
            #pdb.post_mortem(tb)
            import pdb; pdb.set_trace()

    # TODO: remove
    #def generate_tasks(self, init):
        #"""
        #Create new tasks.

        #This method is called on each step of main run cycle and
        #at Spider initialization.

        #initi is True only for call on Spider initialization stage
        #"""

        #pass

    def task_generator(self):
        """
        You can override this method to load new tasks smoothly.

        It will be used each time as number of tasks
        in task queue is less then number of threads multiplied on 1.5
        This allows you to not overload all free memory if total number of
        tasks is big.
        """

        if False:
            # Some magic to make this function generator
            yield ':-)'
        return

    def _preprocess_task(self, task):
        """
        Run custom task preprocessor which could change task
        properties or cancel it.

        This method is called *before* network request.

        Return True to continue process the task or False to cancel the task.
        """

        handler_name = 'preprocess_%s' % task.name
        handler = getattr(self, handler_name, None)
        if handler:
            try:
                return handler(task)
            except Exception, ex:
                self.error_handler(handler_name, ex, task)
                return False
        else:
            return task

    def process_task_generator(self):
        """
        Load new tasks from `self.task_generator_object`
        Create new tasks.

        If task queue size is less than some value
        then load new tasks from tasks file.
        """

        qsize = self.taskq.qsize()
        new_count = 0
        min_limit = int(self.thread_number * 1.5)
        if qsize < min_limit:
            try:
                for x in xrange(min_limit - qsize):
                    self.add_task(self.task_generator_object.next())
                    new_count += 1
            except StopIteration:
                self.task_generator_enabled = False

