import setup_script
from grab.spider import Spider, Task
import logging

class TestSpider(Spider):
    def task_generator(self):
        yield Task('page', url='http://dumpz.org',
                   refresh_cache=True)

    def task_page(self, grab, task):
        print 'downloaded %s' % task.url
        if not task.get('final'):
            yield task.clone(final=True)


def main():
    bot = TestSpider()
    bot.setup_cache(backend='mongo', database='test')
    bot.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()

