import setup_script
from grab.spider import Spider, Task
from grab import Grab
import logging

class TestSpider(Spider):
    def task_generator(self):
        g = self.create_grab_instance()
        g.setup(url='http://h.wrttn.me/status/503', log_dir='log', debug=True)
        yield Task('initial', grab=g)

    def task_initial(self, grab, task):
        print grab.response.code


logging.basicConfig(level=logging.DEBUG)
bot = TestSpider()
bot.setup_grab(debug=True, log_dir='log')
bot.run()
