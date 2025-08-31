from grab.spider import Spider, Task, Data, NoDataHandler

from tests.util import BaseGrabTestCase, build_spider


class TestSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_data_nohandler_error(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                yield Data('foo', num=1)

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        self.assertRaises(NoDataHandler, bot.run)

    def test_exception_from_data_handler(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                yield Data('foo', num=1)

            def data_foo(self, num): # pylint: disable=unused-argument
                raise Exception('Shit happens!')

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertTrue('data_foo' in bot.stat.collections['fatal'][0])

    def test_data_simple_case(self):
        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.data_processed = []

            def task_page(self, unused_grab, unused_task):
                yield Data('foo', number=1)

            def data_foo(self, number):
                self.data_processed.append(number)

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.data_processed, [1])

    def test_complex_data(self):
        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.data_processed = []

            def task_page(self, unused_grab, unused_task):
                yield Data('foo', one=1, two=2, bar='gaz')

            def data_foo(self, one, two, **kwargs):
                self.data_processed.append(one)
                self.data_processed.append(two)
                self.data_processed.append(kwargs)

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.data_processed, [1, 2, {'bar': 'gaz'}])

    def test_data_object_dict_interface(self):
        data = Data('person', person={'age': 22})
        self.assertRaises(KeyError, lambda: data['name'])
        self.assertEqual(data['person'], {'age': 22})

    def test_data_object_get_method(self):
        data = Data('person', person={'age': 22})
        self.assertRaises(KeyError, lambda: data.get('name'))
        self.assertEqual('foo', data.get('name', 'foo'))
        self.assertEqual({'age': 22}, data.get('person'))

    def test_things_yiled_from_data_handler(self):
        server = self.server

        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.data_processed = []

            def task_page(self, unused_grab, task):
                yield Data('foo', count=task.get('count', 1))

            def data_foo(self, count):
                self.data_processed.append(count)
                if count == 1:
                    yield Data('foo', count=666)
                    yield Task('page', url=server.get_url(),
                               count=count + 1)

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.data_processed, [1, 666, 2])
