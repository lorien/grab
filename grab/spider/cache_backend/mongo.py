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
import pymongo
try:
    from bson import Binary
except ImportError:
    from pymongo.binary import Binary
import time

from grab.response import Response
from grab.cookie import CookieManager
from grab.util.py3k_support import *

logger = logging.getLogger('grab.spider.cache_backend.mongo')


class CacheBackend(object):
    def __init__(self, database, use_compression=True, spider=None):
        self.spider = spider
        self.db = pymongo.Connection()[database]
        self.use_compression = use_compression

    def get_item(self, url, timeout=None):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        if timeout is not None:
            ts = int(time.time()) - timeout
            query = {'_id': _hash, 'timestamp': {'$gt': ts}}
        else:
            query = {'_id': _hash}
        return self.db.cache.find_one(query)

    def build_hash(self, url):
        if isinstance(url, unicode):
            utf_url = url.encode('utf-8')
        else:
            utf_url = url
        return sha1(utf_url).hexdigest()

    def remove_cache_item(self, url):
        _hash = self.build_hash(url)
        self.db.cache.remove({'_id': _hash})

    def load_response(self, grab, cache_item):
        grab.fake_response(cache_item['body'])

        body = cache_item['body']
        if self.use_compression:
            body = zlib.decompress(body)

        def custom_prepare_response_func(transport, g):
            response = Response()
            response.head = cache_item['head'].decode('utf-8')
            response.body = body
            response.code = cache_item['response_code']
            response.download_size = len(body)
            response.upload_size = 0
            response.download_speed = 0

            # Hack for deprecated behaviour
            if 'response_url' in cache_item:
                response.url = cache_item['response_url']
            else:
                logger.debug('You cache contains items without `response_url` '
                             'key. It is deprecated data format. Please '
                             're-download you cache or build manually '
                             '`response_url` keys.')
                response.url = cache_item['url']

            response.parse()
            response.cookies = CookieManager(transport.extract_cookiejar())

            return response

        grab.process_request_result(custom_prepare_response_func)

    def save_response(self, url, grab):
        body = grab.response.body
        if self.use_compression:
            body = zlib.compress(body)

        _hash = self.build_hash(url)
        item = {
            '_id': _hash,
            'timestamp': int(time.time()),
            'url': url,
            'response_url': grab.response.url,
            'body': Binary(body),
            'head': Binary(grab.response.head.encode('utf-8')),
            'response_code': grab.response.code,
            'cookies': None,
        }
        try:
            self.db.cache.save(item, safe=True)
        except Exception as ex:
            if 'document too large' in unicode(ex):
                logging.error('Document too large. It was not saved into mongo'
                              ' cache. Url: %s' % url)
            else:
                raise

    def clear(self):
        self.db.cache.remove()
