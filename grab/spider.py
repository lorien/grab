from Queue import PriorityQueue, Empty
import pycurl
from grab import Grab
import logging
import types
from collections import defaultdict
import os
import time
import signal

class SpiderError(Exception):
    "Base class for Spider exceptions"


class SpiderMisuseError(SpiderError):
    "Improper usage of Spider framework"


class Task(object):
    """
    Task for spider.
    """

    def __init__(self, name, url=None, grab=None, priority=100,
                 network_try_count=0, task_try_count=0, **kwargs):
        self.name = name
        if url is None and grab is None:
            raise SpiderMisuseError('Either url of grab option of '\
                                    'Task should be not None')
        self.url = url
        self.grab = grab
        self.priority = priority
        if self.grab:
            self.url = grab.config['url']
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.network_try_count = network_try_count
        self.task_try_count = task_try_count

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

    def __init__(self, thread_number=3, request_limit=None,
                 network_try_limit=10, task_try_limit=10):
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
        self.generate_tasks()
        signal.signal(signal.SIGUSR1, self.sigusr1_handler)

    def sigusr1_handler(self, signal, frame):
        """
        Catches SIGUSR1 signal and dumps current state
        to temporary file
        """

        open('/tmp/spider.state', 'w').write(self.render_stats())


    def load_tasks(self, path, task_name='initial', task_priority=100,
                   limit=None):
        count = 0
        for line in open(path):
            url = line.strip()
            if url:
                self.taskq.put((task_priority, Task(task_name, url)))
                count += 1
                if limit is not None and count >= limit:
                    logging.debug('load_tasks limit reached')
                    break

    def setup_grab(self, **kwargs):
        self.grab_config = kwargs

    def run(self):
        self.start_time = time.time()
        for res in self.fetch():

            # Increase request counter
            self.inc_count('request')

            #if self.counters['request'] and not self.counters['request'] % 100:
                #import guppy; x = guppy.hpy().heap(); import pdb; pdb.set_trace()

            self.generate_tasks()

            if (self.request_limit is not None and
                self.counters['request'] >= self.request_limit):
                logging.debug('Request limit is reached: %s' %\
                              self.request_limit)
                break

            if res is None:
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
                            self.error_handler(handler_name, ex, res['task'])
                        else:
                            if isinstance(result, types.GeneratorType):
                                for item in result:
                                    self.process_result(item, res['task'])
                            else:
                                self.process_result(result, res['task'])
                    else:
                        if self.network_try_limit:
                            task = res['task']
                            task.grab = res['grab_original']
                            result = self.add_task(task)
                            if not result:
                                self.add_item('too-many-network-tries',
                                              res['task'].url)
                        self.inc_count('network-error-%s' % res['emsg'][:20])
                        # TODO: allow to write error handlers

        # This code is executed when main cycles is breaked
        self.shutdown()
    
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

        if task.task_try_count >= self.task_try_limit:
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
        num_processed = 0

        # This is infinite cycle
        # You can break it only from outside code which
        # iterates over result of this method
        while True:
            while True:
                if not freelist:
                    break
                try:
                    priority, task = self.taskq.get(True, 0.1)
                except Empty:
                    # If All handlers are free and no tasks in queue
                    # yield None signal
                    if len(freelist) == self.thread_number:
                        yield None
                    break
                else:
                    curl = freelist.pop()

                    task.network_try_count += 1
                    if task.task_try_count == 0:
                        task.task_try_count = 1

                    if task.grab:
                        grab = task.grab
                    else:
                        # Set up curl instance via Grab interface
                        grab = Grab(**self.grab_config)
                        if self.proxylist_config:
                            args, kwargs = self.proxylist_config
                            grab.setup_proxylist(*args, **kwargs)
                        grab.setup(url=task.url)

                    curl.grab = grab
                    curl.grab.curl = curl
                    curl.grab_original = grab.clone()
                    curl.grab.prepare_request()
                    curl.task = task
                    # Add configured curl instance to multi-curl processor
                    m.add_handle(curl)

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
        grab_original = curl.grab_original

        url = task.url or grab.config['url']
        grab.process_request_result()

        # Break links, free resources
        curl.grab.curl = None
        curl.grab = None
        curl.task = None

        return {'ok': ok, 'grab': grab, 'grab_original': grab_original,
                'task': task,
                'ecode': ecode, 'emsg': emsg}

    def shutdown(self):
        """
        You can override this method to do some final actions
        after parsing has been done.
        """

        logging.debug('Job done!')
        self.total_time = time.time() - self.start_time

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
        # Sort counters by its names
        items = sorted(self.counters.items(), key=lambda x: x[0], reverse=True)
        out.append('  %s\n' % '\n  '.join('%s: %s' % x for x in items))
        out.append('Lists:')
        # Sort lists by number of items
        items = [(x, len(y)) for x, y in self.items.items()]
        items = sorted(items, key=lambda x: x[1], reverse=True)
        out.append('  %s\n' % '\n  '.join('%s: %s' % x for x in items))

        if not hasattr(self, 'total_time'):
            self.total_time = time.time() - self.start_time
        out.append('Time: %.2f sec' % self.total_time)
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

    def generate_tasks(self):
        """
        Create new tasks.

        This method is called on each step of main run cycle and
        at Spider initialization.
        """

        pass

