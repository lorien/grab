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
from bson import Binary
import time
import six
from weblib.encoding import make_str

from grab.response import Response
from grab.cookie import CookieManager

logger = logging.getLogger('grab.spider.cache_backend.mongo')


class CacheBackend(object):
    def __init__(self, database, use_compression=True, spider=None, **kwargs):
        self.spider = spider
        self.db = pymongo.MongoClient(**kwargs)[database]
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
        utf_url = make_str(url)
        return sha1(utf_url).hexdigest()

    def remove_cache_item(self, url):
        _hash = self.build_hash(url)
        self.db.cache.remove({'_id': _hash})

    def load_response(self, grab, cache_item):
        grab.setup_document(cache_item['body'])

        body = cache_item['body']
        if self.use_compression:
            body = zlib.decompress(body)

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
        if self.use_compression:
            body = zlib.compress(body)

        _hash = self.build_hash(url)
        item = {
            '_id': _hash,
            'timestamp': int(time.time()),
            'url': url,
            'response_url': grab.response.url,
            'body': Binary(body),
            'head': Binary(grab.response.head),
            'response_code': grab.response.code,
            'cookies': None,
        }
        try:
            self.db.cache.save(item, w=1)
        except Exception as ex:
            if 'document too large' in six.text_type(ex):
                logging.error('Document too large. It was not saved into mongo'
                              ' cache. Url: %s' % url)
            else:
                raise

    def clear(self):
        self.db.cache.remove()

    def size(self):
        return self.db.cache.count()

    def has_item(self, url, timeout=None):
        """
        Test if required item exists in the cache.
        """

        _hash = self.build_hash(url)
        if timeout is not None:
            ts = int(time.time()) - timeout
            query = {'_id': _hash, 'timestamp': {'$gt': ts}}
        else:
            query = {'_id': _hash}
        doc = self.db.cache.find_one(query, {'id': 1})
        return doc is not None
