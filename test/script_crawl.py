from grab.spider import Spider, Task
from grab.script import crawl
from grab.util.module import SPIDER_REGISTRY

from test.util import TMP_DIR
from test.util import BaseGrabTestCase


class TestSpider(Spider):
    url = None
    points = []

    def prepare(self):
        del self.points[:]

    def task_generator(self):
        yield Task('page', url=self.url)

    def task_page(self, grab, task):
        self.points.append(grab.response.body)



class FailSpider(Spider):
    def task_generator(self):
        yield Task('page', url=self.url)

    def task_page(self, grab, task):
        1/0


class ScriptCrawlTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_crawl(self):
        TestSpider.url = self.server.get_url()
        self.server.response['data'] = b'1'
        SPIDER_REGISTRY.clear()
        crawl.main('test_spider', settings_module='test.files.crawl_settings',
                   disable_report=True)
        self.assertEquals(TestSpider.points, [b'1'])

    def test_crawl_save_lists(self):
        FailSpider.url = self.server.get_url()
        self.server.response['data'] = b'1'
        SPIDER_REGISTRY.clear()
        crawl.main('fail_spider', settings_module='test.files.crawl_settings')
