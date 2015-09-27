# Copyright: 2015, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://getdata.pro)
# License: MIT
from __future__ import absolute_import
import logging
'''
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import random
try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit
import pycurl
import tempfile
import os
from weblib.http import (encode_cookies, normalize_http_values,
                        normalize_post_data, normalize_url)
from weblib.user_agent import random_user_agent
from weblib.encoding import make_str, decode_pairs, make_unicode
import six
from six.moves.http_cookiejar import CookieJar
import sys

from grab.upload import UploadFile, UploadContent
'''
from weblib.http import normalize_url, normalize_post_data
from urllib3 import PoolManager, ProxyManager, exceptions
import six
from six.moves.urllib.parse import urlencode
import tempfile
import os

from grab import error
from grab.cookie import CookieManager#, create_cookie
from grab.response import Response

logger = logging.getLogger('grab.transport.urllib3')

'''
def process_upload_items(items):
    result = []
    for key, val in items:
        if isinstance(val, UploadContent):
            data = [pycurl.FORM_BUFFER, val.filename,
                    pycurl.FORM_BUFFERPTR, val.content]
            if val.content_type:
                data.extend([pycurl.FORM_CONTENTTYPE, val.content_type])
            result.append((key, tuple(data)))
        elif isinstance(val, UploadFile):
            data = [pycurl.FORM_FILE, val.path]
            if val.filename:
                data.extend([pycurl.FORM_FILENAME, val.filename])
            if val.content_type:
                data.extend([pycurl.FORM_CONTENTTYPE, val.content_type])
            result.append((key, tuple(data)))
        else:
            result.append((key, val))
    return result
'''


class Request(object):
    def __init__(self, method=None, url=None, data=None,
                 proxy=None, proxy_userpwd=None, proxy_type=None,
                 headers=None):
        self.url = url
        self.method = method
        self.data = data
        self.proxy = proxy
        self.proxy_userpwd = proxy_userpwd
        self.proxy_type = proxy_type
        self.headers = headers

        self._response_file = None
        self._response_path = None


class Urllib3Transport(object):
    """
    Grab network transport based on urllib3 library.
    """
    def __init__(self):
        self.pool = PoolManager(10)

    def reset(self):
        #self.response_header_chunks = []
        #self.response_body_chunks = []
        #self.response_body_bytes_read = 0
        #self.verbose_logging = False
        #self.body_file = None
        #self.body_path = None
        # Maybe move to super-class???
        self.request_head = ''
        self.request_body = ''
        self.request_log = ''
        self._request = None

    def process_config(self, grab):
        req = Request(data=None)

        try:
            request_url = normalize_url(grab.config['url'])
        except Exception as ex:
            raise error.GrabInvalidUrl(
                u'%s: %s' % (six.text_type(ex), grab.config['url']))
        req.url = request_url

        method = grab.detect_request_method()
        req.method = method

        # Body processing
        if grab.config['body_inmemory']:
            pass
        else:
            if not grab.config['body_storage_dir']:
                raise error.GrabMisuseError(
                    'Option body_storage_dir is not defined')
            file_, path_ = self.setup_body_file(
                grab.config['body_storage_dir'],
                grab.config['body_storage_filename'],
                create_dir=grab.config['body_storage_create_dir'])
            req._response_file = file_
            req._response_path = path_

        if grab.config['multipart_post'] is not None:
            #post_items = normalize_http_values(
            #    grab.config['multipart_post'],
            #    charset=grab.config['charset'],
            #    ignore_classes=(UploadFile, UploadContent),
            #)
            #if six.PY3:
            #    post_items = decode_pairs(post_items,
            #                              grab.config['charset'])
            #self.curl.setopt(pycurl.HTTPPOST,
            #                 process_upload_items(post_items))
            raise Exception('multipart not supported')
        elif grab.config['post'] is not None:
            post_data = normalize_post_data(grab.config['post'],
                                            grab.config['charset'])
            # py3 hack
            # if six.PY3:
            #    post_data = smart_unicode(post_data,
            #                              grab.config['charset'])
            req.data = post_data

        # Proxy
        if grab.config['proxy']:
            req.proxy = grab.config['proxy']

        if grab.config['proxy_userpwd']:
            req.proxy_userpwd = grab.config['proxy_userpwd']

        if grab.config['proxy_type']:
            req.proxy_type = grab.config['proxy_type']
        else:
            req.proxy_type = 'http'

        # Headers
        headers = grab.config['common_headers']
        if grab.config['headers']:
            headers.update(grab.config['headers'])
        req.headers = headers

        self._request = req

    def request(self):
        req = self._request

        if req.proxy:
            if req.proxy_userpwd:
                auth = '%s@' % req.proxy_userpwd
            else:
                auth = ''
            proxy_url = '%s://%s%s' % (req.proxy_type, auth, req.proxy)
            pool = ProxyManager(proxy_url)
        else:
            pool = self.pool
        try:
            res = pool.urlopen(req.method, req.url, body=req.data, timeout=2,
                               retries=False, headers=req.headers)
        except exceptions.ConnectionError as ex:
            raise error.GrabConnectionError(ex.args[1][0], ex.args[1][1])

        # WTF?
        self.request_head = ''
        self.request_body = ''
        self.request_log = ''

        self._response = res
        #raise error.GrabNetworkError(ex.args[0], ex.args[1])
        #raise error.GrabTimeoutError(ex.args[0], ex.args[1])
        #raise error.GrabConnectionError(ex.args[0], ex.args[1])
        #raise error.GrabAuthError(ex.args[0], ex.args[1])
        #raise error.GrabTooManyRedirectsError(ex.args[0],
        #                                      ex.args[1])
        #raise error.GrabCouldNotResolveHostError(ex.args[0],
        #                                         ex.args[1])
        #raise error.GrabNetworkError(ex.args[0], ex.args[1])
        #six.reraise(error.GrabInternalError, error.GrabInternalError(ex),
        #            sys.exc_info()[2])

    def prepare_response(self, grab):
        #if self.body_file:
        #    self.body_file.close()
        response = Response()

        head = ''
        for key, val in self._response.getheaders().items():
            head += '%s: %s\r\n' % (key, val)
        head += '\r\n'
        response.head = head.encode('latin')

        #if self.body_path:
        #    response.body_path = self.body_path
        #else:
        #    response.body = b''.join(self.response_body_chunks)
        if self._request._response_path:
            response.body_path = self._request._response_path
            # Quick dirty hack, actullay, response is ready into memory
            self._request._response_file.write(self._response.data)
            self._request._response_file.close()
        else:
            response.body = self._response.data

        # Clear memory
        #self.response_header_chunks = []

        response.code = self._response.status
        #response.total_time = self.curl.getinfo(pycurl.TOTAL_TIME)
        #response.connect_time = self.curl.getinfo(pycurl.CONNECT_TIME)
        #response.name_lookup_time = self.curl.getinfo(pycurl.NAMELOOKUP_TIME)
        #response.download_size = self.curl.getinfo(pycurl.SIZE_DOWNLOAD)
        #response.upload_size = self.curl.getinfo(pycurl.SIZE_UPLOAD)
        #response.download_speed = self.curl.getinfo(pycurl.SPEED_DOWNLOAD)
        #response.remote_ip = self.curl.getinfo(pycurl.PRIMARY_IP)

        response.url = None#self.curl.getinfo(pycurl.EFFECTIVE_URL)

        import email.message
        hdr = email.message.Message() 
        for key, val in self._response.getheaders().items():
            hdr[key] = val
        response.parse(charset=grab.config['document_charset'],
                       headers=hdr)

        response.cookies = CookieManager()#self.extract_cookiejar())

        # We do not need anymore cookies stored in the
        # curl instance so drop them
        #self.curl.setopt(pycurl.COOKIELIST, 'ALL')
        return response

    def setup_body_file(self, storage_dir, storage_filename, create_dir=False):
        if create_dir:
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)
        if storage_filename is None:
            handle, path = tempfile.mkstemp(dir=storage_dir)
            self.body_file = os.fdopen(handle, 'wb')
        else:
            path = os.path.join(storage_dir, storage_filename)
            self.body_file = open(path, 'wb')
        self.body_path = path
        return self.body_file, self.body_path
