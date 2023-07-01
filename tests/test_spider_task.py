from __future__ import annotations

from collections.abc import Generator

from test_server import Response

from grab import Document, HttpRequest
from grab.errors import GrabMisuseError, ResponseNotValidError
from grab.spider import NoTaskHandlerError, Spider, SpiderMisuseError, Task, base
from grab.spider.errors import SpiderError
from tests.util import BaseTestCase


class SimpleSpider(Spider):
    def task_baz(self, grab: Document, unused_task: Task) -> None:
        pass


class TestSpiderTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_task_priority(self) -> None:
        # Automatic random priority
        base.RANDOM_TASK_PRIORITY_RANGE = (10, 20)
        bot = SimpleSpider(priority_mode="random")
        task = Task("baz", url="http://xxx.com")
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        assert task.priority is not None
        self.assertTrue(10 <= task.priority <= 20)  # noqa: PLR2004

        # Automatic constant priority
        base.DEFAULT_TASK_PRIORITY = 33
        bot = SimpleSpider(priority_mode="const")
        task = Task("baz", url="http://xxx.com")
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertEqual(33, task.priority)

        # Automatic priority does not override explicitly set priority
        base.DEFAULT_TASK_PRIORITY = 33
        bot = SimpleSpider(priority_mode="const")
        task = Task("baz", url="http://xxx.com", priority=1)
        self.assertEqual(1, task.priority)
        bot.add_task(task)
        self.assertEqual(1, task.priority)

        self.assertRaises(SpiderMisuseError, lambda: SimpleSpider(priority_mode="foo"))

    # def test_task_url(self):
    #    bot = SimpleSpider()
    #    task = Task("baz", url="http://xxx.com")
    #    self.assertEqual("http://xxx.com", task.url)
    #    bot.add_task(task)
    #    self.assertEqual("http://xxx.com", task.url)
    #    self.assertEqual(None, task.grab_config)

    #    task = Task("baz", "http://yyy.com")
    #    bot.add_task(task)
    #    self.assertEqual("http://yyy.com", task.url)
    #    self.assertEqual("http://yyy.com", task.grab_config["url"])

    def test_task_clone(self) -> None:
        bot = SimpleSpider()

        task = Task("baz", url="http://xxx.com")
        bot.add_task(task.clone())

        # Pass grab to clone
        task = Task("baz", url="http://xxx.com")
        bot.add_task(task.clone(url="zzz"))

        # Pass grab_config to clone
        task = Task("baz", url="http://xxx.com")
        bot.add_task(task.clone(url="zzz"))

    def test_task_clone_with_url_param(self) -> None:
        task = Task("baz", url="http://example.com/path")
        task2 = task.clone(url="http://example.com/new")
        self.assertEqual(task2.name, "baz")
        self.assertEqual(task2.request.url, "http://example.com/new")

    def test_task_useragent(self) -> None:
        self.server.add_response(Response(), count=1)
        bot = SimpleSpider()

        task = Task(
            "baz",
            HttpRequest(
                method="GET",
                url=self.server.get_url(),
                headers={"User-Agent": "Foo"},
            ),
        )
        bot.add_task(task.clone())
        bot.run()
        self.assertEqual(self.server.request.headers.get("user-agent"), "Foo")

    def test_task_nohandler_error(self) -> None:
        self.server.add_response(Response(), count=1)

        class TestSpider(Spider):
            pass

        bot = TestSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        self.assertRaises(NoTaskHandlerError, bot.run)

    def test_task_raw(self) -> None:
        class TestSpider(Spider):
            def task_page(self, doc: Document, _task: Task) -> None:
                self.collect_runtime_event("codes", str(doc.code))

        self.server.add_response(Response(status=502), count=4)

        bot = TestSpider(network_try_limit=1)
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        self.assertEqual(0, len(bot.runtime_events.get("codes", [])))

        bot = TestSpider(network_try_limit=1)
        bot.add_task(Task("page", url=self.server.get_url(), raw=True))
        bot.add_task(Task("page", url=self.server.get_url(), raw=True))
        bot.run()
        self.assertEqual(2, len(bot.runtime_events["codes"]))

    def test_task_callback(self) -> None:
        self.server.add_response(Response(), count=4)

        class TestSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                self.meta["tokens"].append("0_handler")

        class FuncWithState:
            def __init__(self, tokens: list[str]) -> None:
                self.tokens = tokens

            def __call__(self, _grab: Document, _task: Task) -> None:
                self.tokens.append("1_func")

        tokens: list[str] = []
        func = FuncWithState(tokens)

        bot = TestSpider()
        bot.meta["tokens"] = tokens
        # classic handler
        bot.add_task(Task("page", url=self.server.get_url()))
        # callback option overried classic handler
        bot.add_task(Task("page", url=self.server.get_url(), callback=func))
        # callback and null task name
        bot.add_task(Task(name=None, url=self.server.get_url(), callback=func))
        # callback and default task name
        bot.add_task(Task(url=self.server.get_url(), callback=func))
        bot.run()
        self.assertEqual(["0_handler", "1_func", "1_func", "1_func"], sorted(tokens))

    def test_task_invalid_name(self) -> None:
        self.assertRaises(
            SpiderMisuseError, Task, "generator", url="http://example.com"
        )

    def test_task_constructor_invalid_args(self) -> None:
        # no url, no grab, no grab_config
        with self.assertRaises(GrabMisuseError):
            Task("foo")
        # both url and request
        with self.assertRaises(GrabMisuseError):
            Task("foo", url=1, request=HttpRequest("asdf"))  # type: ignore

    # def test_task_clone_invalid_args(self):
    #    task = Task("foo", url="http://example.com")
    #    # both url and grab
    #    self.assertRaises(SpiderMisuseError, task.clone, url=1, grab=1)
    #    # both url and grab_config
    #    self.assertRaises(SpiderMisuseError, task.clone, url=1, grab_config=1)
    #    # both grab_config and grab
    #    self.assertRaises(SpiderMisuseError, task.clone, grab=1, grab_config=1)

    # def test_task_clone_grab_config_and_url(self):
    #    task = Task("foo", "http://foo.com/")
    #    task2 = task.clone(url="http://bar.com/")
    #    self.assertEqual(task2.request.url, "http://bar.com/")

    # def test_task_clone_kwargs(self):
    #    grab = Grab()
    #    task = Task("foo", HttpRequest("GET", "http://foo.com/", metafoo=1))
    #    task2 = task.clone(foo=2)
    #    self.assertEqual(2, task2.foo)  # pylint: disable=no-member

    def test_task_comparison(self) -> None:
        task1 = Task("foo", url="http://foo.com/", priority=1)
        task2 = Task("foo", url="http://foo.com/", priority=2)
        task3 = Task("foo", url="http://foo.com/")
        # If both tasks have priorities then task are
        # compared by their priorities
        self.assertTrue(task1 < task2)
        # If any of compared tasks does not have priority
        # than tasks are equal
        self.assertTrue(task1 == task3)
        self.assertTrue(task2 == task3)

    def test_task_get_fallback_handler(self) -> None:
        class TestSpider(Spider):
            def do_smth(self, task: Task) -> None:
                pass

            def task_bar_fallback(self, task: Task) -> None:
                pass

        task1 = Task("foo", url="http://foo.com/", fallback_name="do_smth")
        task2 = Task("bar", url="http://foo.com/")
        task3 = Task(url="http://foo.com/")

        bot = TestSpider()

        self.assertEqual(bot.get_fallback_handler(task1), bot.do_smth)
        self.assertEqual(bot.get_fallback_handler(task2), bot.task_bar_fallback)
        self.assertEqual(bot.get_fallback_handler(task3), None)

    # def test_update_grab_instance(self):
    #    self.server.add_response(Response(), count=2)

    #    class TestSpider(Spider):
    #        def update_grab_instance(self, grab):
    #            grab.setup(timeout=77)

    #        def task_generator(self):
    #            yield Task("page", url=self.meta["server"].get_url())
    #            yield Task(
    #                "page",
    #                grab_config=Grab(url=self.meta["server"].get_url(), timeout=1),
    #            )

    #        def task_page(self, grab, unused_task):
    #            self.collect_runtime_event("points", grab.config["timeout"])

    #    bot = TestSpider(meta={"server": self.server})
    #    bot.add_task(Task("page", url=self.server.get_url()))
    #    bot.add_task(
    #        Task(
    #            "page",
    #            HttpRequest(method="GET", url=self.server.get_url(), timeout=1)
    #        )
    #    )
    #    bot.run()
    #    self.assertEqual({77}, set(bot.runtime_events["points"]))

    # def test_create_grab_instance(self):
    #    self.server.add_response(Response(), count=-1)

    #    class TestSpider(Spider):
    #        def create_grab_instance(self, **kwargs):
    #            grab = super().create_grab_instance(**kwargs)
    #            grab.setup(timeout=77)
    #            return grab

    #        def task_generator(self):
    #            yield Task("page", url=self.meta["server"].get_url())
    #            yield Task(
    #                "page",
    #                HttpRequest(
    #                    method="GET",
    #                    url=self.meta["server"].get_url(),
    #                    meta={"foo": 76},
    #                ),
    #            )

    #        def task_page(self, doc, task):
    #            self.collect_runtime_event("points", task.request.meta["foo"])

    #    bot = TestSpider(meta={"server": self.server})
    #    bot.add_task(Task("page", url=self.server.get_url()))
    #    bot.add_task(
    #        Task("page",
    #        HttpRequest(method="GET", url=self.server.get_url(), timeout=75))
    #    )
    #    bot.run()
    #    self.assertEqual({77, 76, 75}, set(bot.runtime_events["points"]))

    def test_add_task_invalid_url_no_error(self) -> None:
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        bot.add_task(Task("page", url="zz://zz"))
        self.assertEqual(0, bot.task_queue.size())
        bot.add_task(Task("page", url="zz://zz"), raise_error=False)
        self.assertEqual(0, bot.task_queue.size())
        bot.add_task(Task("page", url="http://example.com/"))
        self.assertEqual(1, bot.task_queue.size())

    def test_add_task_invalid_url_raise_error(self) -> None:
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        self.assertRaises(
            SpiderError, bot.add_task, Task("page", url="zz://zz"), raise_error=True
        )
        self.assertEqual(0, bot.task_queue.size())
        bot.add_task(Task("page", url="http://example.com/"))
        self.assertEqual(1, bot.task_queue.size())

    def test_worker_restored(self) -> None:
        self.server.add_response(Response(), count=5)

        class TestSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                pass

        bot = TestSpider(parser_requests_per_process=2)
        for _ in range(5):
            bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        self.assertTrue(
            bot.stat.counters["parser:worker-restarted"] == 2  # noqa: PLR2004
        )

    def test_task_clone_post_request(self) -> None:
        self.server.add_response(Response(), count=2)

        class TestSpider(Spider):
            def task_foo(
                self, _doc: Document, _task: Task
            ) -> Generator[Task, None, None]:
                if not task.get("fin"):
                    yield task.clone(fin=True)

        bot = TestSpider()

        task = Task(
            "foo",
            HttpRequest(method="POST", url=self.server.get_url(), fields={"x": "y"}),
        )
        bot.add_task(task)
        bot.run()
        self.assertEqual("POST", self.server.request.method)

    def test_response_not_valid(self) -> None:
        self.server.add_response(Response(), count=-1)

        class SomeSimpleSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                self.stat.inc("xxx")
                raise ResponseNotValidError

        bot = SomeSimpleSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.task_try_limit, bot.stat.counters["xxx"])

    # def test_task_clone_without_modification(self):
    #    self.server.add_response(Response(), count=2)

    #    class TestSpider(Spider):
    #        def task_page(self, grab, task):
    #            yield Task("page2", task.request)

    #        def task_page2(self, grab, task):
    #            pass

    #    bot = TestSpider()
    #    task = Task("page", url=self.server.get_url())
    #    bot.add_task(task)
    #    bot.run()
    #    self.assertEqual(1, bot.stat.counters["spider:task-page"])
    #    self.assertEqual(1, bot.stat.counters["spider:task-page2"])

    def test_task_generator_no_yield(self) -> None:
        self.server.add_response(Response())

        class TestSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                self.stat.inc("foo")

            def task_generator(self) -> Generator[Task, None, None]:
                yield from ()

        bot = TestSpider()
        task = Task("page", url=self.server.get_url())
        bot.add_task(task)
        bot.run()
        self.assertEqual(1, bot.stat.counters["foo"])

    def test_initial_urls(self) -> None:
        self.server.add_response(Response())

        url = self.server.get_url()

        class TestSpider(Spider):
            initial_urls = [url]

            def task_initial(self, _doc: Document, _task: Task) -> None:
                self.stat.inc("foo", 1)

        bot = TestSpider()
        bot.run()

        self.assertEqual(1, bot.stat.counters["foo"])

    def test_constructor_positional_args_name_ok(self) -> None:
        task = Task("baz", HttpRequest("http://yandex.ru"))
        self.assertTrue("yandex" in task.request.url)
