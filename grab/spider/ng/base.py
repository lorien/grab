import grab.spider.base

class BaseNGSpider(grab.spider.base.Spider):
    def __init__(self, result_queue, *args, **kwargs):
        self.result_queue = result_queue
        super(BaseNGSpider, self).__init__(*args, **kwargs)

    def setup_default_queue(self):
        """
        If task queue is not configured explicitly
        then create task queue with default parameters
        """

        if self.taskq is None:
            self.log_verbose('Starting task queue with mongodb backend')
            self.setup_queue(backend='mongo', database='ng_queue',
                             queue_name='task')
