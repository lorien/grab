from Queue import Queue, Empty
import pycurl
from grab import Grab
import logging
import types
from collections import defaultdict

class Request(dict):
    pass


class Content(dict):
    pass


class Bot(object):
    """
    Yet another crapy-like bicycle.
    """

    def __init__(self, initial_urls=None, thread_number=3,
                 initial_task_name='initial', limit=None):
        self.taskq = Queue()
        if initial_urls:
            for url in initial_urls:
                self.taskq.put(Request({'name': initial_task_name, 'url': url}))
        self.thread_number = thread_number
        self.limit = limit
        self.counters = defaultdict(int)
        self.grab_config = {}

    def load_tasks(self, path, task_name='initial', limit=None):
        count = 0
        for line in open(path):
            url = line.strip()
            if url:
                self.taskq.put(Request({'name': task_name, 'url': url}))
                count += 1
                if limit is not None and count >= limit:
                    logging.debug('load_tasks limit reached')
                    break

    def setup_grab(self, **kwargs):
        self.grab_config = kwargs

    def run(self):
        count = 0
        for res in self.fetch():
            count += 1
            if self.limit is not None and count >= self.limit:
                logging.debug('Limit is reached: %s' % self.limit)
                break
            elif res is None:
                logging.debug('Job done!')
                self.shutdown()
                break
            else:
                handler_name = 'parse_%s' % res['task']['name']
                if not hasattr(self, handler_name):
                    raise Exception('Response handler does not exist: %s' % handler_name)
                else:
                    if res['ok']:
                        try:
                            result = getattr(self, handler_name)(res['grab'], res['task'])
                        except Exception, ex:
                            # TODO: what to do with that error?
                            logging.error('', exc_info=ex)
                        else:
                            if isinstance(result, types.GeneratorType):
                                for item in result:
                                    self.process_result(result)
                            else:
                                self.process_result(result)
    
    def process_result(self, result):
        if isinstance(result, Request):
            self.taskq.put(result)
        elif isinstance(result, Content):
            handler_name = 'content_%s' % result['name']
            if not hasattr(self, handler_name):
                handler_name = 'content_default'
            try:
                getattr(self, handler_name)(result) 
            except Exception, ex:
                # TODO: what to do with that error?
                logging.error('', exc_info=ex)
        elif result is None:
            pass
        else:
            raise Exception('Unknown response type: %s' % result)

    def content_default(self, item):
        logging.debug('No content handler for %s content' % item['name'])


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
                    # If All handlers are free and tasks in queue
                    # yield None signal
                    if len(freelist) == self.thread_number:
                        yield None
                    break
                else:
                    curl = freelist.pop()
                    if 'grab' in task:
                        #if 'index.php' in task['grab'].config['url']:
                            #import pdb; pdb.set_trace()
                        curl.grab = task['grab']
                        curl.grab.curl = curl
                    else:
                        # Set up curl instance via Grab interface
                        grab = Grab(**self.grab_config)
                        curl.grab = grab
                        curl.grab.curl = curl
                        curl.grab.setup(url=task['url'])
                    curl.grab.prepare_request()
                    curl._task = task
                    # Add configured curl instance to multi-curl processor
                    m.add_handle(curl)

            while True:
                status, active_objects = m.perform()
                if status != pycurl.E_CALL_MULTI_PERFORM:
                    break

            while True:
                queued_messages, ok_list, fail_list = m.info_read()

                for curl in ok_list:
                    self.inc_count('query')
                    url = curl._task.get('url') or curl._task['grab'].config['url']
                    #logging.debug('OK: %s' % url)
                    curl.grab.process_request_result()
                    # Unbind grab from curl object, maybe does not required
                    curl.grab.curl = None
                    m.remove_handle(curl)
                    freelist.append(curl)
                    yield {'ok': True, 'grab': curl.grab,
                           'task': curl._task}

                for curl, ecode, emsg in fail_list:
                    self.inc_count('query')
                    url = curl._task.get('url') or curl._task['grab'].config['url']
                    #logging.debug('FAIL [%s]: %s' % (emsg, url))
                    curl.grab.process_request_result()
                    # Unbind grab from curl object, maybe does not required
                    curl.grab.curl = None
                    m.remove_handle(curl)
                    freelist.append(curl)
                    yield {'ok': False, 'grab': curl.grab,
                            'task': curl._task, 'ecode': ecode,
                            'emsg': emsg}

                num_processed += (len(ok_list) + len(fail_list))
                if not queued_messages:
                    break

            m.select(0.5)

    def shutdown(self):
        pass

    def inc_count(self, key, step=1):
        self.counters[key] += step
        return self.counters[key]
