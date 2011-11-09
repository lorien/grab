import os
from grab import Grab
from grab.spider import Spider, Task
import logging

print os.getpid()
URL = 'http://load.local/28k.html'
logging.basicConfig(level=logging.DEBUG)

#g = Grab()

#for x in xrange(100):
    #g.go(URL)

class TestSpider(Spider):
    def task_test(self, grab, task):
        print task.url

bot = TestSpider(thread_number=100)
bot.setup_proxylist('/web/blogville/var/awmproxy.txt', 'http',
                    auto_change=True)
for x in xrange(10):
    bot.add_task(Task('test', 'http://ya.ru'))
bot.run()
print 'Done'
print os.getpid()
raw_input()
