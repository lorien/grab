import setup_script

from grab.spider import Spider, Task
from grab.tools.logs import default_logging

class SimpleSpider(Spider):
    def task_generator(self):
        yield Task('page', url='http://ya.ru/')

    def task_page(self, grab, task):
        print grab.doc.select('//title').text()


def main():
    bot = SimpleSpider()
    bot.setup_middleware(['grab.spider.middleware.TestMiddleware'])
    bot.run()
    print bot.render_stats()


if __name__ == '__main__':
    default_logging()
    main()
