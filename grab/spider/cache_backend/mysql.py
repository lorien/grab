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
from hashlib import sha1
import zlib
import logging
import MySQLdb
import marshal
import time
from weblib.encoding import make_str

from grab.response import Response
from grab.cookie import CookieManager

logger = logging.getLogger('grab.spider.cache_backend.mysql')


class CacheBackend(object):
    def __init__(self, database, use_compression=True,
                 mysql_engine='innodb', spider=None, **kwargs):
        self.spider = spider
        self.database = database
        self.connection_config = kwargs
        self.mysql_engine = mysql_engine

        self.connect()
        self.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
        self.execute('show tables')
        found = False
        for row in self.cursor:
            if row[0] == 'cache':
                found = True
                break
        if not found:
            self.create_cache_table(self.mysql_engine)

    def connect(self):
        self.conn = MySQLdb.connect(**self.connection_config)
        self.conn.select_db(self.database)
        self.cursor = self.conn.cursor()

    def execute(self, *args):
        try:
            self.cursor.execute(*args)
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            self.cursor.execute(*args)
        return self.cursor

    def create_cache_table(self, engine):
        self.execute('begin')
        self.execute('''
            create table cache (
                id binary(20) not null,
                timestamp int not null,
                data mediumblob not null,
                primary key (id),
                index timestamp_idx(timestamp)
            ) engine = %s
        ''' % engine)
        self.execute('commit')

    def get_item(self, url, timeout=None):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        with self.spider.timer.log_time('cache.read.mysql_query'):
            self.execute('BEGIN')
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            sql = '''
                  SELECT data
                  FROM cache
                  WHERE id = x%%s %(query)s
                  ''' % {'query': query}
            self.execute(sql, (_hash,))
            row = self.cursor.fetchone()
            self.execute('COMMIT')
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
        self.execute('begin')
        self.execute('''
            delete from cache where id = x%s
        ''', (_hash,))
        self.execute('commit')

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
        _hash = self.build_hash(url)
        data = self.pack_database_value(item)
        self.execute('BEGIN')
        ts = int(time.time())
        sql = '''
              INSERT INTO cache (id, timestamp, data)
              VALUES(x%s, %s, %s)
              ON DUPLICATE KEY UPDATE timestamp = %s, data = %s
              '''
        self.execute(sql, (_hash, ts, data, ts, data))
        self.execute('COMMIT')

    def pack_database_value(self, val):
        dump = marshal.dumps(val)
        return zlib.compress(dump)

    def clear(self):
        self.execute('BEGIN')
        self.execute('TRUNCATE cache')
        self.execute('COMMIT')

    def has_item(self, url, timeout=None):
        """
        Test if required item exists in the cache.
        """

        _hash = self.build_hash(url)
        with self.spider.timer.log_time('cache.read.mysql_query'):
            if timeout is None:
                query = ""
            else:
                ts = int(time.time()) - timeout
                query = " AND timestamp > %d" % ts
            self.execute('BEGIN')
            self.execute('''
                SELECT id
                FROM cache
                WHERE id = x%%s %(query)s
                LIMIT 1
                ''' % {'query': query},
                (_hash,))
            row = self.cursor.fetchone()
            self.execute('COMMIT')
        return True if row else False

    def size(self):
        self.execute('BEGIN')
        self.execute('SELECT COUNT(*) from cache')
        row = self.cursor.fetchone()
        self.execute('COMMIT')
        return row[0]
