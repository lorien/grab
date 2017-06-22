# TODO: implement is_compressed flag
# TODO: close method
"""
CacheItem interface:
'_id': string,
'url': string,
'response_url': string,
'body': string,
'head': string,
'response_code': int,
'cookies': None,#grab.doc.cookies,
"""
from hashlib import sha1
import zlib
import logging
import marshal
import time

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from weblib.encoding import make_str

from grab.document import Document
from grab.cookie import CookieManager

# pylint: disable=invalid-name
logger = logging.getLogger('grab.spider.cache_backend.postgresql')
# pylint: enable=invalid-name


class CacheBackend(object):
    def __init__(self, database, use_compression=True, spider=None, **kwargs):

        self.connection_config = kwargs
        self.database = database
        self.spider = spider
        self.connect()
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

        # FIXME: why `use_compression` is not used?
        self.use_compression = use_compression

    def close(self):
        self.cursor.close()
        self.connection.close()

    def connect(self):
        self.connection = psycopg2.connect(
            dbname=self.database, **self.connection_config
        )
        self.connection.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        self.cursor = self.connection.cursor()

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

    def get_item(self, url):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        self.cursor.execute('BEGIN')
        sql = '''
              SELECT data
              FROM cache
              WHERE id = %s
          '''
        self.cursor.execute(sql, (_hash,))
        row = self.cursor.fetchone()
        self.cursor.execute('COMMIT')
        if row:
            data = row[0]
            return self.unpack_database_value(data)
        else:
            return None

    def unpack_database_value(self, val):
        dump = zlib.decompress(val)
        return marshal.loads(dump)

    def build_hash(self, url):
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
            doc = Document()
            doc.head = cache_item['head']
            doc.body = body
            doc.code = cache_item['response_code']
            doc.download_size = len(body)
            doc.upload_size = 0
            doc.download_speed = 0
            doc.url = cache_item['response_url']
            doc.parse(charset=grab.config['document_charset'])
            doc.cookies = CookieManager(transport.extract_cookiejar())
            doc.from_cache = True
            return doc

        grab.process_request_result(custom_prepare_response_func)

    def save_response(self, url, grab):
        body = grab.doc.body

        item = {
            'url': url,
            'response_url': grab.doc.url,
            'body': body,
            'head': grab.doc.head,
            'response_code': grab.doc.code,
            'cookies': None,
        }
        self.set_item(url, item)

    def set_item(self, url, item):
        _hash = self.build_hash(url)
        data = self.pack_database_value(item)
        self.cursor.execute('BEGIN')
        moment = int(time.time())
        sql = '''
              UPDATE cache SET timestamp = %s, data = %s WHERE id = %s;
              INSERT INTO cache (id, timestamp, data)
              SELECT %s, %s, %s WHERE NOT EXISTS
                (SELECT 1 FROM cache WHERE id = %s);
              '''
        self.cursor.execute(sql, (moment, psycopg2.Binary(data), _hash,
                                  _hash, moment, psycopg2.Binary(data), _hash))
        self.cursor.execute('COMMIT')

    def pack_database_value(self, val):
        dump = marshal.dumps(val)
        return zlib.compress(dump)

    def clear(self):
        self.cursor.execute('BEGIN')
        self.cursor.execute('TRUNCATE cache')
        self.cursor.execute('COMMIT')

    def has_item(self, url):
        """
        Test if required item exists in the cache.
        """

        _hash = self.build_hash(url)
        self.cursor.execute('''
            SELECT id
            FROM cache
            WHERE id = %%s
            LIMIT 1
        ''', (_hash,))
        row = self.cursor.fetchone()
        return True if row else False

    def size(self):
        self.cursor.execute('SELECT COUNT(*) from cache')
        return self.cursor.fetchone()[0]
