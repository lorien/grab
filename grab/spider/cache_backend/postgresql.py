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
from weblib.encoding import make_str

from grab.response import Response
from grab.cookie import CookieManager

logger = logging.getLogger('grab.spider.cache_backend.postgresql')


class CacheBackend(object):
    def __init__(self, database, use_compression=True, spider=None, **kwargs):
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED

        self.spider = spider
        self.conn = psycopg2.connect(dbname=database, **kwargs)
        self.conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            SELECT
                TABLE_NAME
            FROM
                INFORMATION_SCHEMA.TABLES
            WHERE
                TABLE_TYPE = 'BASE TABLE'
            AND
                table_schema NOT IN ('pg_catalog', 'information_schema')""")
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
                data BYTEA NOT NULL
            );
            CREATE INDEX timestamp_idx ON cache (timestamp);
        ''')
        self.cursor.execute('COMMIT')

    def get_item(self, url, timeout=None):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        with self.spider.timer.log_time('cache.read.postgresql_query'):
            self.cursor.execute('BEGIN')
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            sql = '''
                  SELECT data
                  FROM cache
                  WHERE id = %%s %(query)s
                  ''' % {'query': query}
            self.cursor.execute(sql, (_hash,))
            row = self.cursor.fetchone()
            self.cursor.execute('COMMIT')
        if row:
            data = row[0]
            return self.unpack_database_value(data)
        else:
            return None

    def unpack_database_value(self, val):
        with self.spider.timer.log_time('cache.read.unpack_data'):
            dump = zlib.decompress(val)
            return marshal.loads(dump)

    def build_hash(self, url):
        with self.spider.timer.log_time('cache.read.build_hash'):
            utf_url = make_str(url)
            return sha1(utf_url).hexdigest()

    def remove_cache_item(self, url):
        _hash = self.build_hash(url)
        self.cursor.execute('begin')
        self.cursor.execute('''
            DELETE FROM cache WHERE id = %s
        ''', (_hash,))
        self.cursor.execute('commit')

    def load_response(self, grab, cache_item):
        grab.setup_document(cache_item['body'])

        body = cache_item['body']

        def custom_prepare_response_func(transport, grab):
            response = Response()
            response.head = cache_item['head']
            response.body = body
            response.code = cache_item['response_code']
            response.download_size = len(body)
            response.upload_size = 0
            response.download_speed = 0
            response.url = cache_item['response_url']
            response.parse(charset=grab.config['document_charset'])
            response.cookies = CookieManager(transport.extract_cookiejar())
            response.from_cache = True
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
        sql = '''
              UPDATE cache SET timestamp = %s, data = %s WHERE id = %s;
              INSERT INTO cache (id, timestamp, data)
              SELECT %s, %s, %s WHERE NOT EXISTS
                (SELECT 1 FROM cache WHERE id = %s);
              '''
        self.cursor.execute(sql, (ts, psycopg2.Binary(data), _hash,
                            _hash, ts, psycopg2.Binary(data), _hash))
        self.cursor.execute('COMMIT')

    def pack_database_value(self, val):
        dump = marshal.dumps(val)
        return zlib.compress(dump)

    def clear(self):
        self.cursor.execute('BEGIN')
        self.cursor.execute('TRUNCATE cache')
        self.cursor.execute('COMMIT')

    def has_item(self, url, timeout=None):
        """
        Test if required item exists in the cache.
        """

        _hash = self.build_hash(url)
        with self.spider.timer.log_time('cache.read.postgresql_query'):
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            self.cursor.execute('''
                SELECT id
                FROM cache
                WHERE id = %%s %(query)s
                LIMIT 1
                ''' % {'query': query},
                (_hash,))
            row = self.cursor.fetchone()
        return True if row else False

    def size(self):
        self.cursor.execute('SELECT COUNT(*) from cache')
        return self.cursor.fetchone()[0]
