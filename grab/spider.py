from Queue import Queue, Empty
import pycurl
from grab import Grab
import logging
import types
from collections import defaultdict
import os
import time

class SpiderError(Exception):
    "Base class for Spider exceptions"


class SpiderMisuseError(SpiderError):
    "Improper usage of Spider framework"


class Task(object):
    """
    Task for spider.
    """

    def __init__(self, name, url=None, grab=None, **kwargs):
        self.name = name
        if url is None and grab is None:
            raise SpiderMisuseError('Either url of grab option of '\
                                    'Task should be not None')
        self.url = url
        self.grab = grab
        if self.grab:
            self.url = grab.config['url']
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key):
        """
        Return value of attribute or None if such attribute
        does not exist.
        """
        return getattr(self, key, None)


class Data(object):
    """
    Task handlers return result wrapped in the Data class.
    """

    def __init__(self, name, item):
        self.name = name
        self.item = item


class Spider(object):
    """
    Asynchronious scraping framework.
    """

    def __init__(self, initial_urls=None, thread_number=3,
                 initial_task_name='initial', request_limit=None):
        self.taskq = Queue()
        if initial_urls:
            for url in initial_urls:
                self.taskq.put(Task(initial_task_name, url))
        self.thread_number = thread_number
        self.request_limit = request_limit
        self.counters = defaultdict(int)
        self.grab_config = {}
        self.proxylist_config = None
        self.items = {}
        self.history = set()

    def load_tasks(self, path, task_name='initial', limit=None):
        count = 0
        for line in open(path):
            url = line.strip()
            if url:
                self.taskq.put(Task(task_name, url))
                count += 1
                if limit is not None and count >= limit:
                    logging.debug('load_tasks limit reached')
                    break

    def setup_grab(self, **kwargs):
        self.grab_config = kwargs

    def run(self):
        self.start_time = time.time()
        for res in self.fetch():

            if (self.request_limit is not None and
                self.counters['request'] >= self.request_limit):
                logging.debug('Request limit is reached: %s' %\
                              self.request_limit)
                break

            if res is None:
                logging.debug('Job done!')
                self.total_time = time.time() - self.start_time
                self.shutdown()
                break
            else:
                # Increase task counters
                self.inc_count('task')
                self.inc_count('task-%s' % res['task'].name)

                handler_name = 'task_%s' % res['task'].name
                try:
                    handler = getattr(self, handler_name)
                except AttributeError:
                    raise Exception('Task handler does not exist: %s' %\
                                    handler_name)
                else:
                    if res['ok']:
                        try:
                            result = handler(res['grab'], res['task'])
                        except Exception, ex:
                            self.task_error_handler(res['task'], ex)
                        else:
                            if isinstance(result, types.GeneratorType):
                                for item in result:
                                    self.process_result(item)
                            else:
                                self.process_result(result)
    
    def process_result(self, result):
        """
        Process result returned from task handler. 
        Result could be None, Task instance or Data instance.
        """

        if isinstance(result, Task):
            self.add_task(result)
        elif isinstance(result, Data):
            handler_name = 'data_%s' % result.name
            try:
                handler = getattr(self, handler_name)
            except AttributeError:
                handler = self.data_default
            try:
                handler(result.item)
            except Exception, ex:
                self.count_exception(ex)
                logging.error('Error in %s handler' % handler_name,
                              exc_info=ex)
        elif result is None:
            pass
        else:
            raise Exception('Unknown result type: %s' % result)

    def add_task(self, task):
        """
        Add new task to task queue.

        Check that task is new. Only new tasks are added to queue.
        """

        thash = (task.name, task.url)
        if not thash in self.history:
            self.taskq.put(task)
            self.history.add(thash)
        else:
            logging.debug('Task %s -> %s already processed' % (task.name, task.url))
            self.add_item('dup-task', '%s|%s' % (task.name, task.url))

    def data_default(self, item):
        """
        Default handler for Content result for which
        no handler defined.
        """

        logging.debug('Content %s receieved' % item)

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
        num_processed = 0

        # This is infinite cycle
        # You can break it only from outside code which
        # iterates over result of this method
        while True:
            while True:
                if not freelist:
                    break
                try:
                    task = self.taskq.get(True, 0.1)
                except Empty:
                    # If All handlers are free and no tasks in queue
                    # yield None signal
                    if len(freelist) == self.thread_number:
                        yield None
                    break
                else:
                    curl = freelist.pop()

                    if task.grab:
                        grab = task.grab
                        # Do it for consistency
                        # Moved to Task class
                        #task.url = grab.config['url']
                    else:
                        # Set up curl instance via Grab interface
                        grab = Grab(**self.grab_config)
                        if self.proxylist_config:
                            args, kwargs = self.proxylist_config
                            grab.setup_proxylist(*args, **kwargs)
                        grab.setup(url=task.url)

                    curl.grab = grab
                    curl.grab.curl = curl
                    curl.grab.prepare_request()
                    curl.task = task
                    # Add configured curl instance to multi-curl processor
                    m.add_handle(curl)

                    # Increase request counter
                    self.inc_count('request')

            while True:
                status, active_objects = m.perform()
                if status != pycurl.E_CALL_MULTI_PERFORM:
                    break

            while True:
                queued_messages, ok_list, fail_list = m.info_read()
                response_count = 0

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
                    response_count += 1

                num_processed += response_count
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

        url = task.url or grab.config['url']
        grab.process_request_result()

        # Break links, free resources
        curl.grab.curl = None
        curl.grab = None
        curl.task = None

        return {'ok': ok, 'grab': grab, 'task': task,
                'ecode': ecode, 'emsg': emsg}

    def shutdown(self):
        """
        You can override this method to do some final actions
        after parsing has been done.
        """

    def inc_count(self, key, step=1):
        """
        You can call multiply time this method in process of parsing.

        self.inc_count('regurl')
        self.inc_count('captcha')

        and after parsing you can acces to all saved values:

        print 'Total: %(total)s, captcha: %(captcha)s' % spider_obj.counters
        """

        self.counters[key] += step
        return self.counters[key]

    def setup_proxylist(self, *args, **kwargs):
        """
        Save proxylist config which will be later passed to Grab
        constructor.
        """

        self.proxylist_config = (args, kwargs)

    def add_item(self, list_name, item):
        """
        You can call multiply time this method in process of parsing.

        self.add_item('foo', 4)
        self.add_item('foo', 'bar')

        and after parsing you can acces to all saved values:

        spider_instance.items['foo']
        """

        lst = self.items.setdefault(list_name, set())
        lst.add(item)

    def save_list(self, list_name, path):
        """
        Save items from list to the file.
        """

        open(path, 'w').write('\n'.join(self.items.get(list_name, [])))

    def render_stats(self):
        out = []
        out.append('Counters:')
        items = sorted(self.counters.items(), key=lambda x: x[1], reverse=True)
        out.append('  %s' % ', '.join('%s: %s' % x for x in items))
        out.append('Lists:')
        items = [(x, len(y)) for x, y in self.items.items()]
        items = sorted(items, key=lambda x: x[1], reverse=True)
        out.append('  %s' % ', '.join('%s: %s' % x for x in items))
        out.append('Time: %.2f sec' % self.total_time)
        return '\n'.join(out)

    def save_all_lists(self, dir_path):
        """
        Save each list into file in specified diretory.
        """

        for key, items in self.items.items():
            path = os.path.join(dir_path, '%s.txt' % key)
            self.save_list(key, path)

    def task_error_handler(self, task, ex):
        self.inc_count('error-%s' % ex.__class__.__name__.lower())
        self.add_item('fatal', '%s|%s|%s' % (ex.__class__.__name__,
                                             unicode(ex), task.url))
        logging.error('Error in %s handler' % 'task_%s' % task.name,
                      exc_info=ex)

