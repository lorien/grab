from grab.spider import Spider, Task
import logging

class ExampleSpider(Spider):
    def task_generator(self):
        for lang in ('python', 'ruby', 'perl'):
            url = 'https://www.google.com/search?q=%s' % lang
            yield Task('search', url=url)
    
    def task_search(self, grab, task):
        print grab.doc.select('//div[@class="s"]//cite').text()


logging.basicConfig(level=logging.DEBUG)
bot = ExampleSpider()
bot.run()
