from threading import Thread, currentThread
import time
from Queue import Queue, Empty
import logging

STOP = object()


class Worker(Thread):
    def __init__(self, callback, taskq, resultq, ignore_exceptions, *args, **kwargs):
        self.callback = callback
        self.taskq = taskq
        self.resultq = resultq
        self.ignore_exceptions = ignore_exceptions
        Thread.__init__(self, *args, **kwargs)

    def run(self):
        while True:
            task = self.taskq.get()
            if task is STOP:
                return
            else:
                try:
                    self.resultq.put(self.callback(task))
                except Exception, ex:
                    if self.ignore_exceptions:
                        logging.error('', exc_info=ex)
                    else:
                        raise


def make_work(callback, tasks, limit, ignore_exceptions=True,
              taskq_size=50):
    """
    Run up to "limit" threads, do tasks and yield results.

    Arguments:
        callback - the function that will process single task
        tasks - the sequence or iterator or queue of tasks, each task
            in turn is sequence of arguments, if task is just signle argument
            it should be wrapped into list or tuple
        limit - the maximum number of threads
    """
    
    # If tasks is number convert it to the list of number
    if isinstance(tasks, int):
        tasks = xrange(tasks)

    # Ensure that tasks sequence is iterator
    tasks = iter(tasks)    

    taskq= Queue(taskq_size)

    # Here results of task processing will be saved
    resultq= Queue()

    # Prepare and run up to "limit" threads
    threads = []
    for x in xrange(limit):
        thread = Worker(callback, taskq, resultq, ignore_exceptions)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Put tasks from tasks iterator to taskq queue
    # until tasks iterator ends
    # Do it in separate thread
    def task_processor(task_iter, task_queue, limit):
        for task in tasks:
            taskq.put(task)
        for x in xrange(limit):
            taskq.put(STOP)
    processor = Thread(target=task_processor, args=[tasks, taskq, limit])
    processor.daemon = True
    processor.start()

    while True:
        try:
            yield resultq.get(True, 0.2)
        except Empty:
            pass
        if not any(x.isAlive() for x in threads):
            break

    while True:
        try:
            yield resultq.get(False)
        except Empty:
            break



if __name__ == '__main__':
    """
    Usage example
    """

    from threading import currentThread
    import logging
    from random import random
    import time

    def worker(arg):
        logging.debug('Processing %s' % arg)
        time.sleep(random())
        return (currentThread().name, arg)


    def tasks():
        for x in xrange(10):
            logging.debug('Generating task #%d' % x)
            time.sleep(random())
            yield (x,)


    def main():
        for res in make_work(worker, tasks(), 3):
            logging.debug('Result %s received from thread %s' % (res[1], res[0]))


    if __name__ == '__main__':
        logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')
        main()
