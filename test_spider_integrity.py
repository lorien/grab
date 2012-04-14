# coding: utf-8
"""
Quick test to check that Spider refactoring
has not breaked things totally.
"""
from grab.spider import Spider, Task
import pymongo
import logging

db = pymongo.Connection()['spider_test']

class TestSpider(Spider):
    def task_generator(self):
        yield Task('yandex', url='http://yandex.ru/')
        yield Task('google', url='http://google.ru/')
        yield Task('bitbucket_login', url='https://bitbucket.org/account/signin/?next=/')

    def task_yandex(self, grab, task):
        assert grab.xpath_text('//title') == u'Яндекс'
        yield Task('yandex_from_cache', url=task.url)

    def task_yandex_from_cache(self, grab, task):
        assert grab.xpath_text('//title') == u'Яндекс'

    def task_google(self, grab, task):
        assert grab.xpath_text('//title') == u'Google'
        yield Task('google_from_cache', url=task.url)

    def task_google_from_cache(self, grab, task):
        assert grab.xpath_text('//title') == u'Google'

    def task_bitbucket_login(self, grab, task):
        grab.set_input('username', 'grabtest')
        grab.set_input('password', 'grabtest')
        assert grab.xpath_text('//title') == u'Log in to your Bitbucket account'
        grab.submit(make_request=False)
        yield Task('bitbucket_dashboard', grab=grab)

    def task_bitbucket_dashboard(self, grab, task):
        grab.xpath_exists('//li[@id="user-dropdown"]/a/span')
        grab.setup(url='https://bitbucket.org/account/user/grabtest/')
        yield Task('bitbucket_account', grab=grab)

    def task_bitbucket_account(self, grab, task):
        grab.xpath_exists('//input[@value="Save settings"]')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db.cache.remove()
    bot = TestSpider(use_cache=True, cache_db='spider_test',
                     thread_number=4)#, request_limit=2)
    bot.run()
