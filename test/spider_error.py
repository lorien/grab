from grab.spider import Spider, Task
import logging

from test.util import BaseGrabTestCase, build_spider

# That URLs breaks Grab's URL normalization process
# with error "label empty or too long"
INVALID_URL = 'http://13354&altProductId=6423589&productId=6423589'\
              '&altProductStoreId=13713&catalogId=10001'\
              '&categoryId=28678&productStoreId=13713'\
              'http://www.textbooksnow.com/webapp/wcs/stores'\
              '/servlet/ProductDisplay?langId=-1&storeId='


class SpiderErrorTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_generator_with_invalid_url(self):

        class SomeSpider(Spider):
            def task_generator(self):
                yield Task('page', url=INVALID_URL)

        bot = build_spider(SomeSpider)
        bot.run()

    def test_redirect_with_invalid_url(self):

        server = self.server

        class TestSpider(Spider):
            def task_generator(self):
                self.done_counter = 0
                yield Task('page', url=server.get_url())

            def task_page(self, grab, task):
                pass

        self.server.response_once['code'] = 301
        self.server.response_once['headers'] = [
            ('Location', INVALID_URL),
        ]
        bot = build_spider(TestSpider, network_try_limit=1)
        bot.run()

    '''
    # That test case ruins the spider instance :(

    def test_redirect_with_invalid_byte(self):
        url = self.server.get_url()
        invalid_url = b'http://\xa0' + url.encode('ascii')

        def callback(server):
            server.set_status(301)
            server.add_header('Location', invalid_url)
            server.write('')
            server.finish()

        class TestSpider(Spider):
            def task_generator(self):
                #yield Task('page', url='http://www.tripadvisor.com/ShowUrl?&excludeFromVS=false&odc=BusinessListingsUrl&d=4289178&url=1')
                #yield Task('page', invalid_url)
                yield Task('page', url)

            def task_page(self, grab, task):
                pass

        self.server.response['callback'] = callback
        bot = TestSpider()
        bot.run()
    '''
