from abc import abstractmethod
from unittest import TestCase

from test_server import Response

from grab.errors import GrabFeatureIsDeprecated
from grab.spider import Spider, Task
from grab.spider.errors import SpiderMisuseError
from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.queue_backend.memory import MemoryTaskQueue
from tests.util import BaseGrabTestCase, load_test_config


class SpiderQueueMixin:
    class SimpleSpider(Spider):
        def task_page(self, unused_grab, task):
            self.collect_runtime_event("url_history", task.request.url)
            self.collect_runtime_event("priority_history", task.priority)

    @abstractmethod
    def build_task_queue(self) -> BaseTaskQueue:
        raise NotImplementedError

    def test_basic_priority(self):
        self.server.add_response(Response(), count=5)
        bot = self.SimpleSpider(
            parser_pool_size=1,
            thread_number=1,
            task_queue=self.build_task_queue(),
        )
        bot.task_queue.clear()
        requested_urls = {}
        for priority in (4, 2, 1, 5):
            url = self.server.get_url() + "?p=%d" % priority
            requested_urls[priority] = url
            bot.add_task(Task("page", url=url, priority=priority))
        bot.run()
        urls = [x[1] for x in sorted(requested_urls.items(), key=lambda x: x[0])]
        self.assertEqual(urls, bot.runtime_events["url_history"])

    def test_queue_length(self):
        class CustomSpider(self.SimpleSpider):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.final_taskq_size = None

            def shutdown(self):
                self.final_taskq_size = self.task_queue.size()

        self.server.add_response(Response(), count=5)
        bot = CustomSpider(
            task_queue=self.build_task_queue(),
        )
        bot.task_queue.clear()
        for _ in range(5):
            bot.add_task(Task("page", url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.final_taskq_size)

    def test_task_queue_render_stats(self):
        bot = self.SimpleSpider()
        bot.render_stats()

    def test_clear(self):
        bot = self.SimpleSpider(
            task_queue=self.build_task_queue(),
        )
        bot.task_queue.clear()

        for _ in range(5):
            bot.add_task(Task("page", url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.task_queue.clear()
        self.assertEqual(0, bot.task_queue.size())


class SpiderMemoryQueueTestCase(BaseGrabTestCase, SpiderQueueMixin):
    def build_task_queue(self):
        return MemoryTaskQueue()

    def test_schedule(self):
        # In this test I create a number of delayed task
        # and then check the order in which they was executed
        server = self.server
        server.add_response(Response(), count=4)

        class TestSpider(Spider):
            def task_generator(self):
                yield Task("page", url=server.get_url(), delay=1.5, num=3)
                yield Task("page", url=server.get_url(), delay=4.5, num=2)
                yield Task("page", url=server.get_url(), delay=3, num=4)
                yield Task("page", url=server.get_url(), num=1)

            def task_page(self, unused_grab, task):
                self.collect_runtime_event("numbers", task.num)

        bot = TestSpider(thread_number=1)
        bot.run()
        self.assertEqual(bot.runtime_events["numbers"], [1, 3, 4, 2])

    def test_schedule_list_clear(self):
        bot = self.SimpleSpider()
        bot.task_queue.clear()

        for delay in range(5):
            bot.add_task(Task("page", url=self.server.get_url(), delay=delay + 1))

        self.assertEqual(5, len(bot.task_queue.schedule_list))
        bot.task_queue.clear()
        self.assertEqual(0, len(bot.task_queue.schedule_list))


class SpiderMongodbQueueTestCase(SpiderQueueMixin, BaseGrabTestCase):
    backend = "mongodb"

    def build_task_queue(self):
        # pylint: disable=import-outside-toplevel
        from grab.spider.queue_backend.mongodb import MongodbTaskQueue

        return MongodbTaskQueue(
            connection_args=load_test_config()["mongodb_task_queue"]["connection_args"]
        )

    def test_schedule(self):
        # In this test I create a number of delayed task
        # and then check the order in which they was executed
        server = self.server
        server.add_response(Response(), count=4)

        class TestSpider(Spider):
            def task_generator(self):
                yield Task("page", url=server.get_url(), num=1)
                yield Task("page", url=server.get_url(), delay=1.5, num=2)
                yield Task("page", url=server.get_url(), delay=0.5, num=3)
                yield Task("page", url=server.get_url(), delay=1, num=4)

            def task_page(self, unused_grab, task):
                self.collect_runtime_event("numbers", task.num)

        bot = TestSpider(task_queue=self.build_task_queue())
        bot.run()
        self.assertEqual(bot.runtime_events["numbers"], [1, 3, 4, 2])
        # TODO: understand why that test fails

    def test_clear_collection(self):
        bot = self.SimpleSpider(task_queue=self.build_task_queue())
        bot.task_queue.clear()


class SpiderRedisQueueTestCase(SpiderQueueMixin, BaseGrabTestCase):
    backend = "redis"

    def build_task_queue(self):
        # create uniq redis key
        # if use same key then there might be uncleaned
        # data from previous tests
        # pylint: disable=import-outside-toplevel
        from grab.spider.queue_backend.redis import RedisTaskQueue

        return RedisTaskQueue(
            connection_args=load_test_config()["mongodb_task_queue"]["connection_args"],
        )

    def test_delay_error(self):
        bot = self.SimpleSpider(task_queue=self.build_task_queue())
        bot.task_queue.clear()
        self.assertRaises(
            SpiderMisuseError,
            bot.add_task,
            Task("page", url=self.server.get_url(), delay=1),
        )


class TaskQueueTestCase(TestCase):
    class SimpleSpider(Spider):
        pass

    def test_deprecated_setup_queue(self):
        bot = self.SimpleSpider()
        with self.assertRaises(GrabFeatureIsDeprecated):
            bot.setup_queue("foobar")
