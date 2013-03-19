import setup_script

from grab.spider import Spider, Task

class SimpleSpider(Spider):
    def task_generator(self):
        yield Task('page', url='http://ya.ru/')

    def task_page(self, grab, task):
        print grab.doc.select('//title').text()


def main():
    bot = SimpleSpider()
    bot.run()
    print bot.render_stats()


if __name__ == '__main__':
    main()
