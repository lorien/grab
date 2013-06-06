"""
CacheItem interface:
'_id': string,
'url': string,
'response_url': string,
'body': string,
'head': string,
'response_code': int,
'cookies': None,#grab.response.cookies,

TODO: WTF with cookies???
"""
from __future__ import absolute_import
from hashlib import sha1
import zlib
import logging
import MySQLdb
import marshal
import time

from grab.response import Response

logger = logging.getLogger('grab.spider.cache_backend.mysql')


class CacheBackend(object):
    def __init__(self, database, use_compression=True,
                 mysql_engine='innodb', spider=None, **kwargs):
        self.spider = spider
        self.conn = MySQLdb.connect(**kwargs)
        self.mysql_engine = mysql_engine
        self.conn.select_db(database)
        self.cursor = self.conn.cursor()
        self.cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
        res = self.cursor.execute('show tables')
        found = False
        for row in self.cursor:
            if row[0] == 'cache':
                found = True
                break
        if not found:
            self.create_cache_table(self.mysql_engine)

    def create_cache_table(self, engine):
        self.cursor.execute('begin')
        self.cursor.execute('''
            create table cache (
                id binary(20) not null,
                timestamp int not null,
                data mediumblob not null,
                primary key (id),
                index timestamp_idx(timestamp)
            ) engine = %s
        ''' % engine)
        self.cursor.execute('commit')

    def get_item(self, url, timeout=None):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        with self.spider.save_timer('cache.read.mysql_query'):
            self.cursor.execute('BEGIN')
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            res = self.cursor.execute('''
                SELECT data
                FROM cache
                WHERE id = x%%s %(query)s
                ''' % {'query': query},
                (_hash,))
            row = self.cursor.fetchone()
            self.cursor.execute('COMMIT')
        if row:
            return self.unpack_database_value(row[0])
        else:
            return None

    def unpack_database_value(self, val):
        with self.spider.save_timer('cache.read.unpack_data'):
            dump = zlib.decompress(val)
            return marshal.loads(dump)

    def build_hash(self, url):
        with self.spider.save_timer('cache.read.build_hash'):
            if isinstance(url, unicode):
                utf_url = url.encode('utf-8')
            else:
                utf_url = url
            return sha1(utf_url).hexdigest()

    def remove_cache_item(self, url):
        _hash = self.build_hash(url)
        self.cursor.execute('begin')
        self.cursor.execute('''
            delete from cache where id = x%s
        ''', (_hash,))
        self.cursor.execute('commit')

    def load_response(self, grab, cache_item):
        grab.fake_response(cache_item['body'])

        body = cache_item['body']

        def custom_prepare_response_func(transport, g):
            response = Response()
            response.head = cache_item['head']
            response.body = body
            response.code = cache_item['response_code']
            response.time = 0

            # Hack for deprecated behaviour
            if 'response_url' in cache_item:
                response.url = cache_item['response_url']
            else:
                logger.debug('You cache contains items without `response_url` key. It is depricated data format. Please re-download you cache or build manually `response_url` keys.')
                response.url = cache_item['url']

            response.parse()
            response.cookies = transport.extract_cookies()
            return response

        grab.process_request_result(custom_prepare_response_func)

    def save_response(self, url, grab):
        body = grab.response.body

        item = {
            'url': url,
            'response_url': grab.response.url,
            'body': body,
            'head': grab.response.head,
            'response_code': grab.response.code,
            'cookies': None,
        }
        self.set_item(url, item)

    def set_item(self, url, item):
        _hash = self.build_hash(url)
        data = self.pack_database_value(item)
        self.cursor.execute('BEGIN')
        ts = int(time.time())
        res = self.cursor.execute('''
            INSERT INTO cache (id, timestamp, data)
            VALUES(x%s, %s, %s)
            ON DUPLICATE KEY UPDATE timestamp = %s, data = %s
        ''', (_hash, ts, data, ts, data))
        self.cursor.execute('COMMIT')

    def pack_database_value(self, val):
        dump = marshal.dumps(val)
        return zlib.compress(dump)

    def clear(self):
        self.cursor.execute('BEGIN')
        self.cursor.execute('TRUNCATE cache')
        self.cursor.execute('COMMIT')
