import mock

from six import StringIO

from grab import GrabTimeoutError, Grab
from grab.spider import Spider, Task
from tests.util import BaseGrabTestCase, build_spider, run_test_if, GLOBAL

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
                # pylint: disable=attribute-defined-outside-init
                self.done_counter = 0
                # pylint: enable=attribute-defined-outside-init
                yield Task('page', url=server.get_url())

            def task_page(self, grab, task):
                pass

        self.server.response_once['code'] = 301
        self.server.response_once['headers'] = [
            ('Location', INVALID_URL),
        ]
        bot = build_spider(TestSpider, network_try_limit=1)
        bot.run()

    # FIXME: fix
    # That test case ruins the spider instance :(
    #def test_redirect_with_invalid_byte(self):
    #    url = self.server.get_url()
    #    invalid_url = b'http://\xa0' + url.encode('ascii')

    #    def callback(server):
    #        server.set_status(301)
    #        server.add_header('Location', invalid_url)
    #        server.write('')
    #        server.finish()

    #    class TestSpider(Spider):
    #        def task_generator(self):
    #        #yield Task('page', url='http://www.tripadvisor.com/ShowUrl?
    #        #&excludeFromVS=false&odc=BusinessListingsUrl&d=4289178&url=1')
    #            #yield Task('page', invalid_url)
    #            yield Task('page', url)
    #
    #        def task_page(self, grab, task):
    #            pass
    #
    #    self.server.response['callback'] = callback
    #    bot = build_spider(TestSpider)
    #    bot.run()

    def test_no_warning(self):
        """Simple spider should not generate
        any warnings (warning module sends messages to stderr)
        """
        out = StringIO()
        with mock.patch('sys.stderr', out):
            server = self.server
            server.response['data'] = b'<div>test</div>'

            class SimpleSpider(Spider):
                # pylint: disable=unused-argument
                initial_urls = [server.get_url()]

                def task_initial(self, grab, task):
                    yield Task('more', url=server.get_url())

                def task_more(self, grab, task):
                    #print(grab.doc.url)
                    grab.doc('//div').text()

            bot = build_spider(SimpleSpider)
            bot.run()
        self.assertTrue(out.getvalue() == '')

    def test_grab_attribute_exception(self):
        server = self.server
        server.response['sleep'] = 2

        class SimpleSpider(Spider):

            def task_generator(self):
                grab = Grab()
                grab.setup(url=server.get_url(),
                           timeout=1)
                yield Task('page', grab=grab,
                           raw=True)

            def task_page(self, grab, unused_task):
                self.meta['exc'] = grab.exception

        bot = build_spider(SimpleSpider)
        bot.run()
        self.assertTrue(isinstance(bot.meta['exc'], GrabTimeoutError))

    @run_test_if(lambda: (GLOBAL['network_service'] == 'multicurl'
                          and GLOBAL['grab_transport'] == 'pycurl'),
                 'multicurl & pycurl')
    def test_stat_error_name_multi_pycurl(self):

        server = self.server
        server.response['sleep'] = 2

        class SimpleSpider(Spider):
            def prepare(self):
                self.network_try_limit = 1

            def task_generator(self):
                grab = Grab(url=server.get_url(), timeout=1)
                yield Task('page', grab=grab)

            def task_page(self, grab, unused_task):
                pass

        bot = build_spider(SimpleSpider)
        bot.run()
        self.assertTrue('error:operation-timeouted' in bot.stat.counters)

    @run_test_if(lambda: (GLOBAL['network_service'] == 'threaded'
                          and GLOBAL['grab_transport'] == 'pycurl'),
                 'threaded & pycurl')
    def test_stat_error_name_threaded_pycurl(self):

        server = self.server
        server.response['sleep'] = 2

        class SimpleSpider(Spider):
            def prepare(self):
                self.network_try_limit = 1

            def task_generator(self):
                grab = Grab(url=server.get_url(), timeout=1)
                yield Task('page', grab=grab)

            def task_page(self, grab, unused_task):
                pass

        bot = build_spider(SimpleSpider)
        bot.run()
        print(bot.stat.counters)
        self.assertTrue('error:grab-timeout-error' in bot.stat.counters)

    @run_test_if(lambda: (GLOBAL['network_service'] == 'threaded'
                          and GLOBAL['grab_transport'] == 'urllib3'),
                 'threaded & urllib3')
    def test_stat_error_name_threaded_urllib3(self):

        server = self.server
        server.response['sleep'] = 2

        class SimpleSpider(Spider):
            def prepare(self):
                self.network_try_limit = 1

            def task_generator(self):
                grab = Grab(url=server.get_url(), timeout=1)
                yield Task('page', grab=grab)

            def task_page(self, grab, unused_task):
                pass

        bot = build_spider(SimpleSpider)
        bot.run()
        self.assertTrue('error:read-timeout-error' in bot.stat.counters)
