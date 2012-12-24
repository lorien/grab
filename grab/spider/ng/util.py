from multiprocessing import Process

from .worker import BaseWorkerSpider
from .manager import BaseManagerSpider

#class SpiderProcess(Process):
    #def __init__(self, spider_cls, result_queue, *args, **kwargs):
        #self.bot = spider_cls(result_queue)
        #self.cls = cls
        #self.result_queue = result_queue
        #super(SpiderProcess, self).__init__(*args, **kwargs)

    #def run(self):
        #self.bot = bot.run()


def create_process(spider_cls, result_queue, *args, **kwargs):
    # Create spider instance which will performe
    # actions specific to given role
    bot = spider_cls(result_queue, *args, **kwargs)

    # Return Process object binded to the `bot.run` method
    return Process(target=bot.run)
