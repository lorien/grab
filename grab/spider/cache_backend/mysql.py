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

from grab.response import Response

logger = logging.getLogger('grab.spider.cache_backend.mysql')


class CacheBackend(object):
    def __init__(self, database, use_compression=True, **kwargs):
        self.conn = MySQLdb.connect(**kwargs)
        self.conn.select_db(database)
        self.cursor = self.conn.cursor()
        res = self.cursor.execute('show tables')
        found = False
        for row in self.cursor:
            if row[0] == 'cache':
                found = True
                break
        if not found:
            self.create_cache_table()

    def create_cache_table(self):
        self.cursor.execute('''
            create table cache (
                id binary(20) not null,
                data mediumblob not null,
                primary key (id)
            ) engine = myisam
        ''')

    def get_item(self, url):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        res = self.cursor.execute('''
            select data from cache where id = x%s
        ''', (_hash,))
        row = self.cursor.fetchone()
        if row:
            return self.unpack_database_value(row[0])
        else:
            return None

    def unpack_database_value(self, val):
        dump = zlib.decompress(val)
        return marshal.loads(dump)

    def build_hash(self, url):
        if isinstance(url, unicode):
            utf_url = url.encode('utf-8')
        else:
            utf_url = url
        return sha1(utf_url).hexdigest()

    def remove_cache_item(self, url):
        _hash = self.build_hash(url)
        self.cursor.execute('''
            delete from cache where id = x%s
        ''', (_hash,))

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
        res = self.cursor.execute('''
            insert into cache (id, data) values(x%s, %s)
            on duplicate key update data = %s
        ''', (_hash, data, data))

    def pack_database_value(self, val):
        dump = marshal.dumps(val)
        return zlib.compress(dump)
