#!/usr/bin/env python
# coding: utf-8
from grab.spider import Spider, Task
from grab.tools.logs import default_logging
from grab import Grab
import pymongo
import logging
from urlparse import urlsplit, parse_qs, parse_qsl, urlunsplit, urljoin
from grab.tools.lxml_tools import parse_html, render_html, drop_node, clone_node
import traceback
import urllib
from collections import defaultdict
import re

class DefaultSpider(Spider):
    initial_urls = ['http://desconto.ru/']
    base_url = 'http://desconto.ru'

    def task_initial(self, grab, task):
        print 'title', grab.xpath_text('//title', '')
        for elem in grab.xpath_list('//a'):
            yield Task('page', url=elem.get('href'))

    def task_page(self, grab, task):
        print 'title', grab.xpath_text('//title', '')


def main():
    import sys 
    default_logging()
    cls = globals()[sys.argv[1] if len(sys.argv) > 1 else 'DefaultSpider']
    bot = cls(thread_number=1)
    bot.setup_cache(
        backend='mysql',
        database='encdic_cache',
        use_compression=True,
        user='web', passwd='web-**'
    )
    #bot.setup_cache(
        #backend='mongo',
        #database='spider_test',
        #use_compression=True,
    #)
    #bot.load_proxylist('/web/proxy.txt', 'text_file')
    try:
        bot.run()
    except KeyboardInterrupt:
        pass
    #bot.save_all_lists('var')
    bot.save_list('fatal', 'var/fatal.txt')
    print bot.render_stats()


if __name__ == '__main__':
    main()
