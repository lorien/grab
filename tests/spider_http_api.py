from threading import Thread
import socket
import time

from six.moves.urllib.request import urlopen

from grab.spider import Spider, Task
from tests.util import BaseGrabTestCase, build_spider


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def get_open_port(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", 0))
        sock.listen(1)
        port = sock.getsockname()[1]
        sock.close()
        return port

    def test_spider(self):

        class SimpleSpider(Spider):
            def task_page(self, grab, unused_task):
                pass

        api_port = self.get_open_port()
        bot = build_spider(
            SimpleSpider, http_api_port=api_port,
        )
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(),
                          delay=1))

        def worker():
            bot.run()

        th = Thread(target=worker) # pylint: disable=invalid-name
        th.daemon = True
        th.start()

        time.sleep(0.5)
        data = urlopen('http://localhost:%d' % api_port).read()
        self.assertTrue(b'<title>Grab Api</title>' in data)
