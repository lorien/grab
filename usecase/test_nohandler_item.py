import setup_script
from grab.spider import Spider, Task, Data
from grab.tools.logs import default_logging

class TestSpider(Spider):
    initial_urls = ['http://yandex.ru/robots.txt']

    def task_initial(self, grab, task):
        yield Data('foo', dict(name='Alice'))


default_logging()
bot = TestSpider()
bot.run()
