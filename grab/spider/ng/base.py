import grab.spider.base
import time
import logging

logger = logging.getLogger('spider.ng.base')

class BaseNGSpider(grab.spider.base.Spider):
    def __init__(self, wating_shutdown_event, taskq, result_queue, response_queue, shutdown_event,
                 generator_done_event, *args, **kwargs):
        self.wating_shutdown_event = wating_shutdown_event
        self.taskq = taskq
        self.result_queue = result_queue
        self.shutdown_event = shutdown_event
        self.generator_done_event = generator_done_event
        self.response_queue = response_queue
        super(BaseNGSpider, self).__init__(*args, **kwargs)

        # Fix behaviour of super init method which nulls the `self.taskq`
        self.taskq = taskq
