"""
CacheItem interface:
'url': string,
'response_url': string,
'body': string,
'head': string,
'response_code': int,
'cookies': None,#grab.response.cookies,

TODO: Cookie support???
"""
import tc
import os
import logging
import marshal

from grab.response import Response
from grab.util.py3k_support import *

logger = logging.getLogger('grab.spider.cache_backend.mongo')


def tc_open(path, mode='a+', compress=True, makedirs=True):
    if makedirs:
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass

    db = tc.HDB()
    if compress:
        db.tune(-1, -1, -1, tc.HDBTDEFLATE)
    db.open(path,
        {
            'r': tc.HDBOREADER,
            'w': tc.HDBOWRITER | tc.HDBOCREAT | tc.HDBOTRUNC,
            'a': tc.HDBOWRITER,
            'a+': tc.HDBOWRITER | tc.HDBOCREAT,
        }[mode]
    )
    return db


class CacheBackend(object):
    def __init__(self, database, use_compression=True, spider=None):
        # database == filename
        self.spider = spider
        self.db = tc_open(database, compress=use_compression)
        self.use_compression = use_compression

    def get_item(self, url, timeout=None):
        """
        Returned item should have specific interface. See module docstring.
        """

        if timeout is None:
            raise NotImplemented('timeout option for tokyo cabinet cache '
                                 'backend is not supported')
        try:
            dump = self.db[self.build_key(url)]
        except KeyError:
            return
        return marshal.loads(dump)

    def build_key(self, url):
        return url.encode('utf-8') if isinstance(url, unicode) else url

    def remove_cache_item(self, url):
        del self.db[self.build_key(url)]

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
                logger.debug('You cache contains items without `response_url` '
                             'key. It is deprecated data format. Please '
                             're-download you cache or build manually '
                             '`response_url` keys.')
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
        self.db[self.build_key(url)] = marshal.dumps(item)

    def clear(self):
        raise NotImplemented
