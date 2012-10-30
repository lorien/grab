#!/usr/bin/env python
import MySQLdb
import pymongo
from grab.spider.cache_backend import mysql
import zlib

db = pymongo.Connection()['spider_test']

def main():
    backend = mysql.CacheBackend('encdic_cache', user='web',
                                 passwd='web-**')
    conn = backend.conn
    conn.execute(
    for item in db.cache.find(timeout=False):
        mysql_item = {
            'url': item['url'],
            'response_url': item['response_url'],
            'body': zlib.decompress(item['body']),
            'head': item['head'],
            'response_code': item['response_code'],
            'cookies': item['cookies'],
        }
        backend.set_item(mysql_item['url'], mysql_item)
        print '.',

    print


if __name__ == '__main__':
    main()
