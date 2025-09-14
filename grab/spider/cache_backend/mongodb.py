"""
CacheItem interface:
'_id': string,
'url': string,
'response_url': string,
'body': string,
'head': string,
'response_code': int,
'cookies': None,#grab.doc.cookies,

TODO: WTF with cookies???
"""
import logging
import time
import zlib
from hashlib import sha1

import pymongo
import six
from bson import Binary
from weblib.encoding import make_str

from grab.cookie import CookieManager
from grab.document import Document

# pylint: disable=invalid-name
logger = logging.getLogger("grab.spider.cache_backend.mongodb")
# pylint: enable=invalid-name


class CacheBackend(object):
    def __init__(self, database, use_compression=False, spider=None, **kwargs):
        self.colname = "cache"
        self.dbname = database
        self.spider = spider
        self.init_kwargs = kwargs
        self.connect()
        self.connection, self.db, self.collection = self.connect()
        self.use_compression = use_compression

    def connect(self):
        connection = pymongo.MongoClient(**self.init_kwargs)
        db = connection[self.dbname]
        collection = db[self.colname]
        return connection, db, collection

    def reconnect(self):
        self.connection, self.db, self.collection = self.connect()

    def close(self):
        self.connection.close()

    def get_item(self, url):
        """
        Returned item should have specific interface. See module docstring.
        """

        _hash = self.build_hash(url)
        query = {"_id": _hash}
        return self.collection.find_one(query)

    def build_hash(self, url):
        utf_url = make_str(url)
        return sha1(utf_url).hexdigest()

    def remove_cache_item(self, url):
        _hash = self.build_hash(url)
        self.collection.delete_one({"_id": _hash})

    def load_response(self, grab, cache_item):
        grab.setup_document(cache_item["body"])

        body = cache_item["body"]
        # Till the 0.6.39 version there was no compressed flag
        # so it was possible to detected the compressed item
        # only by analyzing the byte stream
        try:
            is_compressed = cache_item["is_compressed"]
        except KeyError:
            is_compressed = body[0] == 120
        if is_compressed:
            body = zlib.decompress(body)

        def custom_prepare_response_func(transport, grab):
            doc = Document()
            doc.head = cache_item["head"]
            doc.body = body
            doc.code = cache_item["response_code"]
            doc.download_size = len(body)
            doc.upload_size = 0
            doc.download_speed = 0
            doc.url = cache_item["response_url"]
            doc.parse(charset=grab.config["document_charset"])
            doc.cookies = CookieManager(transport.extract_cookiejar())
            doc.from_cache = True
            return doc

        grab.process_request_result(custom_prepare_response_func)

    def save_response(self, url, grab):
        body = grab.doc.body
        if self.use_compression:
            body = zlib.compress(body)

        _hash = self.build_hash(url)
        item = {
            "_id": _hash,
            "timestamp": int(time.time()),
            "url": url,
            "response_url": grab.doc.url,
            "body": Binary(body),
            "head": Binary(grab.doc.head),
            "response_code": grab.doc.code,
            "cookies": None,
            "is_compressed": self.use_compression,
        }
        # print('Before saving')
        try:
            self.collection.insert_one(item)
        except Exception as ex:  # pylint: disable=broad-except
            # from traceback import format_exc
            # print('FATA ERROR WHILE SAVING CACHE ITEM')
            # print(format_exc())
            if "document too large" in six.text_type(ex):
                logging.error(
                    "Document too large. It was not saved into"
                    " mongodb cache. Url: %s",
                    url,
                )
            else:
                raise
        # else:
        #    print('COUNT: %d' % self.collection.count({'_id': item['_id']}))
        # finally:
        #    print('After saving')

    def clear(self):
        self.collection.delete_many({})

    def size(self):
        return self.collection.count_documents({})

    def has_item(self, url):
        """
        Test if required item exists in the cache.
        """

        _hash = self.build_hash(url)
        query = {"_id": _hash}
        doc = self.collection.find_one(query, {"id": 1})
        return doc is not None
