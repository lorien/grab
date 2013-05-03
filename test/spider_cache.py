from unittest import TestCase
import pymongo

from grab.spider import Spider, Task
from .tornado_util import SERVER

db = pymongo.Connection()['spider_test']

def build_html():
    return """
    <head>
        <title>ABC</title>
    </head>
    <body>
        <a href="%(BASE_URL)s/">link #1</a>
        <a href="%(BASE_URL)s/">link #2</a>
    </body>
    """ % {'BASE_URL': SERVER.BASE_URL}

class SimpleSpider(Spider):
    def task_foo(self, grab, task):
        grab.setup(url=SERVER.BASE_URL)
        yield Task('bar', grab=grab)
        for elem in grab.doc.select('//a'):
            yield Task('bar', url=elem.attr('href'))

    def task_bar(self, grab, task):
        pass


class TestSpiderCache(TestCase):
    def setUp(self):
        SERVER.reset()
        SERVER.RESPONSE['get'] = build_html()

    def test_bug1(self):
        """
        Test the bug:
        * enable cache
        * fetch document (it goes to cache)
        * request same URL
        * got exception
        """

        class Bug1Spider(Spider):
            def task_foo(self, grab, task):
                grab.setup(url=SERVER.BASE_URL)
                yield Task('bar', grab=grab)

            def task_bar(self, grab, task):
                pass

        db.cache.remove({})
        bot = Bug1Spider()
        bot.setup_cache(backend='mongo', database='spider_test')
        bot.setup_queue()
        bot.add_task(Task('foo', SERVER.BASE_URL))
        bot.run()


    def test_mysql_cache(self):
        db.cache.remove({})
        bot = SimpleSpider()
        bot.setup_cache(backend='mysql', database='spider_test',
                        user='web', passwd='web-**')
        bot.setup_queue()
        bot.add_task(Task('foo', SERVER.BASE_URL))
        bot.run()


    def test_mysql_cache(self):
        db.cache.remove({})
        bot = SimpleSpider()
        bot.setup_cache(backend='mongo', database='spider_test')
        bot.setup_queue()
        bot.add_task(Task('foo', SERVER.BASE_URL))
        bot.run()
