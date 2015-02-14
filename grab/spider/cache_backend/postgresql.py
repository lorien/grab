"""
CacheItem interface:
'_id': string,
'url': string,
'response_url': string,
'body': string,
'head': string,
'response_code': int,
'cookies': None,#grab.response.cookies,
"""
from hashlib import sha1
import zlib
import logging
import marshal
import time

from grab.response import Response
from grab.cookie import CookieManager
from grab.util.py3k_support import *


logger = logging.getLogger('grab.spider.cache_backend.postgresql')

class CacheBackend(object):
    def __init__(self, database, use_compression=True, spider=None, **kwargs):
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED

        self.spider = spider
        self.conn = psycopg2.connect(dbname=database, **kwargs)
        self.conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        self.cursor = self.conn.cursor()
        res = self.cursor.execute("""
            SELECT
                TABLE_NAME
            FROM
                INFORMATION_SCHEMA.TABLES
            WHERE
                TABLE_TYPE = 'BASE TABLE'
            AND
                table_schema NOT IN ('pg_catalog', 'information_schema')"""
        )
        found = False
        for row in self.cursor:
            if row[0] == 'cache':
                found = True
                break
        if not found:
            self.create_cache_table()

    def create_cache_table(self):
        self.cursor.execute('BEGIN')
        self.cursor.execute('''
            CREATE TABLE cache (
                id BYTEA NOT NULL CONSTRAINT primary_key PRIMARY KEY,
                timestamp INT NOT NULL,
                data BYTEA NOT NULL,
            );
            CREATE INDEX timestamp_idx ON cache (timestamp);
        ''')
        self.cursor.execute('COMMIT')

    def get_item(self, url, timeout=None):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        with self.spider.save_timer('cache.read.postgresql_query'):
            self.cursor.execute('BEGIN')
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            # py3 hack
            if PY3K:
                sql = '''
                      SELECT data
                      FROM cache
                      WHERE id = {0} %(query)s
                      ''' % {'query': query}
            else:
                sql = '''
                      SELECT data
                      FROM cache
                      WHERE id = %%s %(query)s
                      ''' % {'query': query}
            res = self.cursor.execute(sql, (_hash,))
            row = self.cursor.fetchone()
            self.cursor.execute('COMMIT')
        if row:
            data = row[0]
            return self.unpack_database_value(data)
        else:
            return None

    def unpack_database_value(self, val):
        with self.spider.save_timer('cache.read.unpack_data'):
            dump = zlib.decompress(str(val))
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
            DELETE FROM cache WHERE id = x%s
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
            response.download_size = len(body)
            response.upload_size = 0
            response.download_speed = 0

            # Hack for deprecated behaviour
            if 'response_url' in cache_item:
                response.url = cache_item['response_url']
            else:
                logger.debug('You cache contains items without '
                             '`response_url` key. It is deprecated data '
                             'format. Please re-download you cache or '
                             'build manually `response_url` keys.')
                response.url = cache_item['url']

            response.parse()
            response.cookies = CookieManager(transport.extract_cookiejar())
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
        import psycopg2

        _hash = self.build_hash(url)
        data = self.pack_database_value(item)
        self.cursor.execute('BEGIN')
        ts = int(time.time())
        # py3 hack
        if PY3K:
            sql = '''
                  UPDATE cache SET timestamp = {0}, data = {1} WHERE id = {2};
                  INSERT INTO cache (id, timestamp, data)
                  SELECT {2}, {0}, {1} WHERE NOT EXISTS (SELECT 1 FROM cache WHERE id = {2});
                  '''
        else:
            sql = '''
                  UPDATE cache SET timestamp = %s, data = %s WHERE id = %s;
                  INSERT INTO cache (id, timestamp, data)
                  SELECT %s, %s, %s WHERE NOT EXISTS (SELECT 1 FROM cache WHERE id = %s);
                  '''
        res = self.cursor.execute(sql, (ts, psycopg2.Binary(data), _hash,
                                        _hash, ts, psycopg2.Binary(data),
                                        _hash))
        self.cursor.execute('COMMIT')

    def pack_database_value(self, val):
        dump = marshal.dumps(val)
        return  zlib.compress(dump)

    def clear(self):
        self.cursor.execute('BEGIN')
        self.cursor.execute('TRUNCATE cache')
        self.cursor.execute('COMMIT')

    def has_item(self, url, timeout=None):
        """
        Test if required item exists in the cache.
        """

        _hash = self.build_hash(url)
        with self.spider.save_timer('cache.read.postgresql_query'):
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            res = self.cursor.execute('''
                SELECT id
                FROM cache
                WHERE id = %%s %(query)s
                LIMIT 1
                ''' % {'query': query},
                (_hash,))
            row = self.cursor.fetchone()
        return True if row else False
