from grab.spider import Spider, Task
from grab.script import crawl
from grab.util.module import SPIDER_REGISTRY

from tests.util import BaseGrabTestCase, only_grab_transport


class TestSpider(Spider):
    url = None
    points = []

    def prepare(self):
        #from grab.spider.base import logger_verbose
        #logger_verbose.setLevel(logging.DEBUG)
        del self.points[:]

    def task_generator(self):
        #print('A')
        yield Task('page', url=self.url)

    def task_page(self, grab, unused_task):
        #print('B')
        self.points.append(grab.doc.body)


class FailSpider(Spider):
    def task_generator(self):
        yield Task('page', url=self.url)

    def task_page(self, unused_grab, unused_task):
        raise Exception('Shit happens!')


class ScriptCrawlTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    @only_grab_transport('never')
    def test_crawl(self):
        TestSpider.url = self.server.get_url()
        self.server.response['data'] = b'1'
        SPIDER_REGISTRY.clear()
        crawl.main('test_spider', settings_module='tests.files.crawl_settings',
                   disable_report=True)
        self.assertEqual(TestSpider.points, [b'1'])

    @only_grab_transport('never')
    def test_crawl_save_lists(self):
        FailSpider.url = self.server.get_url()
        self.server.response['data'] = b'1'
        SPIDER_REGISTRY.clear()
        crawl.main('fail_spider', settings_module='tests.files.crawl_settings')
