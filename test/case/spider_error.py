from unittest import TestCase

import grab.spider.base
from grab import Grab
from grab.spider import Spider, Task, Data, SpiderMisuseError, NoTaskHandler
from grab.error import GrabInvalidUrl
import logging

from test.server import SERVER

# That URLs breaks Grab's URL normalization process with error "label empty or too long"
INVALID_URL = 'http://13354&altProductId=6423589&productId=6423589&altProductStoreId=13713&catalogId=10001&categoryId=28678&productStoreId=13713http://www.textbooksnow.com/webapp/wcs/stores/servlet/ProductDisplay?langId=-1&storeId='

class SpiderErrorTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_generator_with_invalid_url(self):

        class SomeSpider(Spider):
            def task_generator(self):
                yield Task('page', url=INVALID_URL)

        from grab.spider.base import logger_verbose
        logger_verbose.setLevel(logging.DEBUG)
        bot = SomeSpider()
        bot.run()

    def test_redirect_with_invalid_url(self):

        class SomeSpider(Spider):
            def task_generator(self):
                self.done_counter = 0
                yield Task('page', url=SERVER.BASE_URL)

            def task_page(self, grab, task):
                pass

        #from grab.spider.base import logger_verbose
        #logger_verbose.setLevel(logging.DEBUG)
        SERVER.RESPONSE_ONCE['code'] = 301
        SERVER.RESPONSE_ONCE['headers'].append(
            ('Location', INVALID_URL),
        )
        bot = SomeSpider(network_try_limit=1)
        bot.run()
