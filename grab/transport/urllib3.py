# Copyright: 2015, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://getdata.pro)
# License: MIT
from __future__ import absolute_import
import logging
import random
import time

from six.moves.urllib.parse import urlsplit
from six.moves.http_cookiejar import CookieJar
import six
from weblib.http import (normalize_url, normalize_post_data,
                         normalize_http_values)
from weblib.encoding import make_str, make_unicode, decode_pairs
from urllib3 import PoolManager, ProxyManager, exceptions, make_headers
from urllib3.filepost import encode_multipart_formdata
from urllib3.fields import RequestField
from urllib3.util.retry import Retry
from urllib3.util.timeout import Timeout
from urllib3.contrib.socks import SOCKSProxyManager
from user_agent import generate_user_agent
import certifi

from grab import error
from grab.error import GrabMisuseError, GrabTimeoutError
from grab.cookie import CookieManager, MockRequest, MockResponse
from grab.document import Document
from grab.upload import UploadFile, UploadContent
from grab.transport.base import BaseTransport


def process_upload_items(items):
    result = []
    for key, val in items:
        if isinstance(val, UploadContent):
            headers = {'Content-Type': val.content_type}
            field = RequestField(name=key, data=val.content,
                                 filename=val.filename, headers=headers)
            field.make_multipart(content_type=val.content_type)
            result.append(field)
        elif isinstance(val, UploadFile):
            data = open(val.path, 'rb').read()
            headers = {'Content-Type': val.content_type}
            field = RequestField(name=key, data=data,
                                 filename=val.filename, headers=headers)
            field.make_multipart(content_type=val.content_type)
            result.append(field)
        else:
            result.append((key, val))
    return result


class Request(object):
    def __init__(self, method=None, url=None, data=None,
                 proxy=None, proxy_userpwd=None, proxy_type=None,
                 headers=None, body_maxsize=None):
        self.url = url
        self.method = method
        self.data = data
        self.proxy = proxy
        self.proxy_userpwd = proxy_userpwd
        self.proxy_type = proxy_type
        self.headers = headers
        self.body_maxsize = body_maxsize
        self.op_started = None
        self.timeout = None
        self.connect_timeout = None
        self.config_nobody = None
        self.config_body_maxsize = None

        self.response_file = None
        self.response_path = None

    def get_full_url(self):
        return self.url


class Urllib3Transport(BaseTransport):
    """
    Grab network transport based on urllib3 library.
    """
    def __init__(self):
        super(Urllib3Transport, self).__init__()
        # http://urllib3.readthedocs.io/en/latest/user-guide.html#certificate-verification
        self.pool = PoolManager(
            10,
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )

        logger = logging.getLogger('urllib3.connectionpool')
        logger.setLevel(logging.WARNING)

        self.request_head = b''
        self.request_body = b''
        self.request_log = b''

        self._response = None
        self._request = None

    def reset(self):
        #self.response_header_chunks = []
        #self.response_body_chunks = []
        #self.response_body_bytes_read = 0
        #self.verbose_logging = False
        #self.body_file = None
        #self.body_path = None
        # Maybe move to super-class???
        self.request_head = b''
        self.request_body = b''
        self.request_log = b''

        self._response = None
        self._request = None

    def process_config(self, grab):
        req = Request(data=None)

        try:
            request_url = normalize_url(grab.config['url'])
        except Exception as ex:
            raise error.GrabInvalidUrl(
                u'%s: %s' % (
                    six.text_type(ex),
                    make_unicode(grab.config['url'], errors='ignore')
                )
            )
        req.url = request_url

        method = grab.detect_request_method()
        req.method = make_str(method)

        req.config_body_maxsize = grab.config['body_maxsize']
        req.config_nobody = grab.config['nobody']

        req.timeout = grab.config['timeout']
        req.connect_timeout = grab.config['connect_timeout']

        extra_headers = {}

        # Body processing
        if grab.config['body_inmemory']:
            pass
        else:
            if not grab.config['body_storage_dir']:
                raise GrabMisuseError(
                    'Option body_storage_dir is not defined')
            file_, path_ = self.setup_body_file(
                grab.config['body_storage_dir'],
                grab.config['body_storage_filename'],
                create_dir=grab.config['body_storage_create_dir'])
            req.response_file = file_
            req.response_path = path_

        if grab.config['multipart_post'] is not None:
            post_data = grab.config['multipart_post']
            if isinstance(post_data, six.binary_type):
                pass
            elif isinstance(post_data, six.text_type):
                raise GrabMisuseError('Option multipart_post data'
                                      ' does not accept unicode.')
            else:
                post_items = normalize_http_values(
                    grab.config['multipart_post'],
                    charset=grab.config['charset'],
                    ignore_classes=(UploadFile, UploadContent),
                )
                post_items = decode_pairs(post_items,
                                          grab.config['charset'])
                post_items = process_upload_items(post_items)
                post_data, content_type = encode_multipart_formdata(post_items)
                extra_headers['Content-Type'] = content_type
            extra_headers['Content-Length'] = len(post_data)
            req.data = post_data
        elif grab.config['post'] is not None:
            post_data = normalize_post_data(grab.config['post'],
                                            grab.config['charset'])
            # py3 hack
            # if six.PY3:
            #    post_data = smart_unicode(post_data,
            #                              grab.config['charset'])
            extra_headers['Content-Length'] = len(post_data)
            req.data = post_data

        if method in ('POST', 'PUT'):
            if (grab.config['post'] is None
                    and grab.config['multipart_post'] is None):
                raise GrabMisuseError('Neither `post` or `multipart_post`'
                                      ' options was specified for the %s'
                                      ' request' % method)
        # Proxy
        if grab.config['proxy']:
            req.proxy = grab.config['proxy']

        if grab.config['proxy_userpwd']:
            req.proxy_userpwd = grab.config['proxy_userpwd']

        if grab.config['proxy_type']:
            req.proxy_type = grab.config['proxy_type']
        else:
            req.proxy_type = 'http'

        # User-Agent
        if grab.config['user_agent'] is None:
            if grab.config['user_agent_file'] is not None:
                with open(grab.config['user_agent_file']) as inf:
                    lines = inf.read().splitlines()
                grab.config['user_agent'] = random.choice(lines)
            else:
                grab.config['user_agent'] = generate_user_agent()

        extra_headers['User-Agent'] = grab.config['user_agent']

        # Headers
        headers = extra_headers
        headers.update(grab.config['common_headers'])

        if grab.config['headers']:
            headers.update(grab.config['headers'])
        req.headers = headers

        # Cookies
        self.process_cookie_options(grab, req)

        self._request = req

    def request(self):
        req = self._request

        if req.proxy:
            if req.proxy_userpwd:
                headers = make_headers(proxy_basic_auth=req.proxy_userpwd)
            else:
                headers = None
            proxy_url = '%s://%s' % (req.proxy_type, req.proxy)
            if req.proxy_type == 'socks5':
                pool = SOCKSProxyManager(
                    proxy_url,
                    cert_reqs='CERT_REQUIRED',
                    ca_certs=certifi.where()
                ) # , proxy_headers=headers)
            else:
                pool = ProxyManager(
                    proxy_url, proxy_headers=headers,
                    cert_reqs='CERT_REQUIRED',
                    ca_certs=certifi.where()
                )
        else:
            pool = self.pool
        try:
            # Retries can be disabled by passing False:
            # http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry
            # Do not use False because of warning:
            # Converted retries value: False -> Retry(total=False,
            # connect=None, read=None, redirect=0, status=None)
            retry = Retry(
                total=False,
                connect=False,
                read=False,
                redirect=0,
                status=None,
            )
            # The read timeout is not total response time timeout
            # It is the timeout on read of next data chunk from the server
            # Total response timeout is handled by Grab
            timeout = Timeout(connect=req.connect_timeout,
                              read=req.timeout)
            #req_headers = dict((make_unicode(x), make_unicode(y))
            #                   for (x, y) in req.headers.items())
            if six.PY3:
                req_url = make_unicode(req.url)
                req_method = make_unicode(req.method)
            else:
                req_url = make_str(req.url)
                req_method = req.method
            req.op_started = time.time()
            try:
                res = pool.urlopen(req_method,
                                   req_url,
                                   body=req.data, timeout=timeout,
                                   retries=retry,
                                   headers=req.headers,
                                   preload_content=False)
            except UnicodeError as ex:
                raise error.GrabConnectionError('GrabInvalidUrl', ex)
        except exceptions.ReadTimeoutError as ex:
            raise error.GrabTimeoutError('ReadTimeoutError', ex)
        except exceptions.ConnectTimeoutError as ex:
            raise error.GrabConnectionError('ConnectTimeoutError', ex)
        except exceptions.ProtocolError as ex:
            # TODO:
            # the code
            # raise error.GrabConnectionError(ex.args[1][0], ex.args[1][1])
            # fails
            # with error TypeError: 'OSError' object is not subscriptable
            raise error.GrabConnectionError('ProtocolError', ex)
        except exceptions.SSLError as ex:
            raise error.GrabConnectionError('SSLError', ex)

        # WTF?
        self.request_head = b''
        self.request_body = b''
        self.request_log = b''

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
        # Information about urllib3
        # On python2 urllib3 headers contains original binary data
        # On python3 urllib3 headers are converted to unicode
        # using latin encoding
        try:
            #if self.body_file:
            #    self.body_file.close()
            response = Document()

            head = ''
            for key, val in self._response.getheaders().items():
                if six.PY2:
                    key = key.decode('utf-8', errors='ignore')
                    val = val.decode('utf-8', errors='ignore')
                if six.PY3:
                    key = key.encode('latin').decode('utf-8', errors='ignore')
                    val = val.encode('latin').decode('utf-8', errors='ignore')
                head += '%s: %s\r\n' % (key, val)
            head += '\r\n'
            response.head = make_str(head, encoding='utf-8')

            #if self.body_path:
            #    response.body_path = self.body_path
            #else:
            #    response.body = b''.join(self.response_body_chunks)
            def read_with_timeout():
                if self._request.config_nobody:
                    return b''
                maxsize = self._request.config_body_maxsize
                chunks = []
                default_chunk_size = 10000
                if maxsize:
                    chunk_size = min(default_chunk_size, maxsize + 1)
                else:
                    chunk_size = default_chunk_size
                bytes_read = 0
                while True:
                    chunk = self._response.read(chunk_size)
                    if chunk:
                        bytes_read += len(chunk)
                        chunks.append(chunk)
                        if maxsize and bytes_read > maxsize:
                            # reached limit on bytes to read
                            break
                    else:
                        break
                    if self._request.timeout:
                        if (time.time() - self._request.op_started
                                > self._request.timeout):
                            raise GrabTimeoutError
                data = b''.join(chunks)
                if maxsize:
                    data = data[:maxsize]
                return data

            if self._request.response_path:
                response.body_path = self._request.response_path
                # FIXME: Quick dirty hack, actullay, response is fully
                # read into memory
                self._request.response_file.write(read_with_timeout())
                self._request.response_file.close()
            else:
                response.body = read_with_timeout()

            # Clear memory
            #self.response_header_chunks = []

            response.code = self._response.status
            #response.total_time = self.curl.getinfo(pycurl.TOTAL_TIME)
            #response.connect_time = self.curl.getinfo(pycurl.CONNECT_TIME)
            #response.name_lookup_time = (self.curl
            #                             .getinfo(pycurl.NAMELOOKUP_TIME))
            #response.download_size = self.curl.getinfo(pycurl.SIZE_DOWNLOAD)
            #response.upload_size = self.curl.getinfo(pycurl.SIZE_UPLOAD)
            #response.download_speed = self.curl.getinfo(pycurl.SPEED_DOWNLOAD)
            #response.remote_ip = self.curl.getinfo(pycurl.PRIMARY_IP)

            response.url = (self._response.get_redirect_location()
                            or self._request.url)

            import email.message
            hdr = email.message.Message()
            for key, val in self._response.getheaders().items():
                if six.PY2:
                    key = key.decode('utf-8', errors='ignore')
                    val = val.decode('utf-8', errors='ignore')
                if six.PY3:
                    key = key.encode('latin').decode('utf-8', errors='ignore')
                    val = val.encode('latin').decode('utf-8', errors='ignore')
                #if key == 'Location':
                #    import pdb; pdb.set_trace()
                hdr[key] = val
            response.parse(charset=grab.config['document_charset'],
                           headers=hdr)

            jar = self.extract_cookiejar() # self._response, self._request)
            response.cookies = CookieManager(jar)

            # We do not need anymore cookies stored in the
            # curl instance so drop them
            #self.curl.setopt(pycurl.COOKIELIST, 'ALL')
            return response
        finally:
            self._response.release_conn()

    def extract_cookiejar(self):
        jar = CookieJar()
        # self._respose could be None
        # if this method is called from custom preapre response
        # function called from spider cache backend
        if self._response and self._request:
            jar.extract_cookies(
                # pylint: disable=protected-access
                MockResponse(self._response._original_response.msg),
                # pylint: enable=protected-access
                MockRequest(self._request),
            )
        return jar

    def process_cookie_options(self, grab, req):
        # `cookiefile` option should be processed before `cookies` option
        # because `load_cookies` updates `cookies` option
        if grab.config['cookiefile']:
            # Do not raise exception if cookie file does not exist
            try:
                grab.cookies.load_from_file(grab.config['cookiefile'])
            except IOError as ex:
                logging.error(ex)

        request_host = urlsplit(req.url).hostname
        if request_host:
            if request_host.startswith('www.'):
                request_host_no_www = request_host[4:]
            else:
                request_host_no_www = request_host

            # Process `cookies` option that is simple dict i.e.
            # it provides only `name` and `value` attributes of cookie
            # No domain, no path, no expires, etc
            # I pass these no-domain cookies to *each* requested domain
            # by setting these cookies with corresponding domain attribute
            # Trying to guess better domain name by removing leading "www."
            if grab.config['cookies']:
                if not isinstance(grab.config['cookies'], dict):
                    raise error.GrabMisuseError('cookies option should'
                                                ' be a dict')
                for name, value in grab.config['cookies'].items():
                    grab.cookies.set(
                        name=name,
                        value=value,
                        domain=request_host_no_www
                    )

        cookie_hdr = grab.cookies.get_cookie_header(req)
        if cookie_hdr:
            req.headers['Cookie'] = cookie_hdr
