# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import logging
# import urllib
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
from weblib.http import (normalize_http_values,
                         normalize_post_data, normalize_url)
from weblib.encoding import make_str, decode_pairs
import six
from six.moves.http_cookiejar import CookieJar
import sys
from user_agent import generate_user_agent

from grab.cookie import create_cookie, CookieManager
from grab import error
from grab.error import GrabMisuseError
from grab.response import Response
from grab.upload import UploadFile, UploadContent
from grab.transport.base import BaseTransport

logger = logging.getLogger('grab.transport.curl')

# @lorien: I do not understand these signals. Maybe you?

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.

# http://curl.haxx.se/mail/curlpython-2005-06/0004.html
# http://curl.haxx.se/mail/lib-2010-03/0114.html

# CURLOPT_NOSIGNAL
# Pass a long. If it is 1, libcurl will not use any functions that install
# signal handlers or any functions that cause signals to be sent to the
# process. This option is mainly here to allow multi-threaded unix applications
# to still set/use all timeout options etc, without risking getting signals.
# (Added in 7.10)

# If this option is set and libcurl has been built with the standard name
# resolver, timeouts will not occur while the name resolve takes place.
# Consider building libcurl with c-ares support to enable
# asynchronous DNS
# lookups, which enables nice timeouts for name resolves without signals.

try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    try:
        signal.signal(SIGPIPE, SIG_IGN)
    except ValueError:
        # Ignore the exception
        # ValueError: signal only works in main thread
        pass
except ImportError:
    pass


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


class CurlTransport(BaseTransport):
    """
    Grab transport layer using pycurl.
    """

    def __init__(self):
        self.curl = pycurl.Curl()

    def reset(self):
        super(CurlTransport, self).reset()

        self.response_header_chunks = []
        self.response_body_chunks = []
        self.response_body_bytes_read = 0
        self.verbose_logging = False

        # Maybe move to super-class???
        self.request_head = b''
        self.request_body = b''
        #self.request_log = ''

    def header_processor(self, chunk):
        """
        Process head of response.
        """

        self.response_header_chunks.append(chunk)
        # Returning None implies that all bytes were written
        return None

    def body_processor(self, chunk):
        """
        Process body of response.
        """

        if self.config_nobody:
            self.curl._callback_interrupted = True
            return 0

        bytes_read = len(chunk)

        self.response_body_bytes_read += bytes_read
        if self.body_file:
            self.body_file.write(chunk)
        else:
            self.response_body_chunks.append(chunk)
        if self.config_body_maxsize is not None:
            if self.response_body_bytes_read > self.config_body_maxsize:
                logger.debug('Response body max size limit reached: %s' %
                             self.config_body_maxsize)
                self.curl._callback_interrupted = True
                return 0

        # Returning None implies that all bytes were written
        return None

    def debug_processor(self, _type, text):
        """
        Process request details.

        0: CURLINFO_TEXT
        1: CURLINFO_HEADER_IN
        2: CURLINFO_HEADER_OUT
        3: CURLINFO_DATA_IN
        4: CURLINFO_DATA_OUT
        5: CURLINFO_unrecognized_type
        """
        if _type == pycurl.INFOTYPE_HEADER_OUT:
            if isinstance(text, six.text_type):
                text = text.encode('utf-8')
            self.request_head += text

        if _type == pycurl.INFOTYPE_DATA_OUT:
            # Untill 7.19.5.2 version
            # pycurl gives unicode in `text` variable
            # WTF??? Probably that codes would fails
            # or does unexpected things if you use
            # pycurl<7.19.5.2
            if isinstance(text, six.text_type):
                text = text.encode('utf-8')
            self.request_body += text

        """
        if _type == pycurl.INFOTYPE_TEXT:
            if self.request_log is None:
                self.request_log = ''
            self.request_log += text
        """

        if self.verbose_logging:
            if _type in (pycurl.INFOTYPE_TEXT, pycurl.INFOTYPE_HEADER_IN,
                         pycurl.INFOTYPE_HEADER_OUT):
                marker_types = {
                    pycurl.INFOTYPE_TEXT: 'i',
                    pycurl.INFOTYPE_HEADER_IN: '<',
                    pycurl.INFOTYPE_HEADER_OUT: '>',
                }
                marker = marker_types[_type]
                logger.debug('%s: %s' % (marker, text.rstrip()))

    def process_config(self, grab):
        """
        Setup curl instance with values from ``self.config``.
        """

        # Copy some config for future usage
        self.config_nobody = grab.config['nobody']
        self.config_body_maxsize = grab.config['body_maxsize']

        try:
            request_url = normalize_url(grab.config['url'])
        except Exception as ex:
            raise error.GrabInvalidUrl(
                u'%s: %s' % (six.text_type(ex), grab.config['url']))

        # py3 hack
        if not six.PY3:
            request_url = make_str(request_url)

        self.curl.setopt(pycurl.URL, request_url)

        # Actually, FOLLOWLOCATION should always be 0
        # because redirect logic takes place in Grab.request method
        # BUT in Grab.Spider this method is not invoked
        # So, in Grab.Spider we still rely on Grab internal ability
        # to follow 30X Locations
        self.curl.setopt(pycurl.FOLLOWLOCATION,
                         1 if grab.config['follow_location'] else 0)
        self.curl.setopt(pycurl.MAXREDIRS, grab.config['redirect_limit'])
        self.curl.setopt(pycurl.CONNECTTIMEOUT, grab.config['connect_timeout'])
        self.curl.setopt(pycurl.TIMEOUT, grab.config['timeout'])
        #self.curl.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)
        # self.curl.setopt(pycurl.DNS_CACHE_TIMEOUT, 0)
        if not grab.config['connection_reuse']:
            self.curl.setopt(pycurl.FRESH_CONNECT, 1)
            self.curl.setopt(pycurl.FORBID_REUSE, 1)

        self.curl.setopt(pycurl.NOSIGNAL, 1)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.header_processor)

        if grab.config['body_inmemory']:
            self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        else:
            if not grab.config['body_storage_dir']:
                raise error.GrabMisuseError(
                    'Option body_storage_dir is not defined')
            self.setup_body_file(
                grab.config['body_storage_dir'],
                grab.config['body_storage_filename'],
                create_dir=grab.config['body_storage_create_dir'])
            self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)

        if grab.config['verbose_logging']:
            self.verbose_logging = True

        # User-Agent
        if grab.config['user_agent'] is None:
            if grab.config['user_agent_file'] is not None:
                with open(grab.config['user_agent_file']) as inf:
                    lines = inf.read().splitlines()
                grab.config['user_agent'] = random.choice(lines)
            else:
                grab.config['user_agent'] = generate_user_agent()

        # If value is None then set empty string
        # None is not acceptable because in such case
        # pycurl will set its default user agent "PycURL/x.xx.x"
        if not grab.config['user_agent']:
            grab.config['user_agent'] = ''

        self.curl.setopt(pycurl.USERAGENT, grab.config['user_agent'])

        if grab.config['debug']:
            self.curl.setopt(pycurl.VERBOSE, 1)
            self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        # Ignore SSL errors
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        # Disabled to avoid SSL3_READ_BYTES:sslv3 alert handshake failure error
        # self.curl.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_SSLv3)

        if grab.request_method in ('POST', 'PUT'):
            if (grab.config['post'] is None and
                grab.config['multipart_post'] is None):
                    raise GrabMisuseError('Neither `post` or `multipart_post`'
                                          ' options was specified for the %s'
                                          ' request' % grab.request_method)

        if grab.request_method == 'POST':
            self.curl.setopt(pycurl.POST, 1)
            if grab.config['multipart_post']:
                if isinstance(grab.config['multipart_post'], six.string_types):
                    raise error.GrabMisuseError(
                        'multipart_post option could not be a string')
                post_items = normalize_http_values(
                    grab.config['multipart_post'],
                    charset=grab.config['charset'],
                    ignore_classes=(UploadFile, UploadContent),
                )
                # py3 hack
                #if six.PY3:
                #    post_items = decode_pairs(post_items,
                #                              grab.config['charset'])
                self.curl.setopt(pycurl.HTTPPOST,
                                 process_upload_items(post_items))
            elif grab.config['post']:
                post_data = normalize_post_data(grab.config['post'],
                                                grab.config['charset'])
                # py3 hack
                # if six.PY3:
                #    post_data = smart_unicode(post_data,
                #                              grab.config['charset'])
                self.curl.setopt(pycurl.POSTFIELDS, post_data)
            else:
                self.curl.setopt(pycurl.POSTFIELDS, '')
        elif grab.request_method == 'PUT':
            data = grab.config['post']
            if isinstance(data, six.text_type):
                # py3 hack
                # if six.PY3:
                #    data = data.encode('utf-8')
                # else:
                raise error.GrabMisuseError(
                    'Value of post option could be only '
                    'byte string if PUT method is used')
            self.curl.setopt(pycurl.UPLOAD, 1)
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'PUT')
            self.curl.setopt(pycurl.READFUNCTION, StringIO(data).read)
            self.curl.setopt(pycurl.INFILESIZE, len(data))
        elif grab.request_method == 'PATCH':
            data = grab.config['post']
            if isinstance(data, six.text_type):
                raise error.GrabMisuseError(
                    'Value of post option could be only byte '
                    'string if PATCH method is used')
            self.curl.setopt(pycurl.UPLOAD, 1)
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'PATCH')
            self.curl.setopt(pycurl.READFUNCTION, StringIO(data).read)
            self.curl.setopt(pycurl.INFILESIZE, len(data))
        elif grab.request_method == 'DELETE':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'DELETE')
        elif grab.request_method == 'HEAD':
            self.curl.setopt(pycurl.NOBODY, 1)
        elif grab.request_method == 'UPLOAD':
            self.curl.setopt(pycurl.UPLOAD, 1)
        elif grab.request_method == 'GET':
            self.curl.setopt(pycurl.HTTPGET, 1)
        elif grab.request_method == 'OPTIONS':
            data = grab.config['post']
            if data is not None:
                if isinstance(data, six.text_type):
                    raise error.GrabMisuseError(
                        'Value of post option could be only byte '
                        'string if PATCH method is used')
                self.curl.setopt(pycurl.UPLOAD, 1)
                self.curl.setopt(pycurl.READFUNCTION, StringIO(data).read)
                self.curl.setopt(pycurl.INFILESIZE, len(data))
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'OPTIONS')
        else:
            raise error.GrabMisuseError('Invalid method: %s' %
                                        grab.request_method)

        headers = grab.config['common_headers']
        if grab.config['headers']:
            headers.update(grab.config['headers'])
        # This is required to avoid some problems
        headers.update({'Expect': ''})
        header_tuples = [str('%s: %s' % x) for x
                         in headers.items()]
        self.curl.setopt(pycurl.HTTPHEADER, header_tuples)

        self.process_cookie_options(grab, request_url)

        if grab.config['referer']:
            self.curl.setopt(pycurl.REFERER, str(grab.config['referer']))

        if grab.config['proxy']:
            self.curl.setopt(pycurl.PROXY, str(grab.config['proxy']))
        else:
            self.curl.setopt(pycurl.PROXY, '')

        if grab.config['proxy_userpwd']:
            self.curl.setopt(pycurl.PROXYUSERPWD,
                             str(grab.config['proxy_userpwd']))

        if grab.config['proxy_type']:
            key = 'PROXYTYPE_%s' % grab.config['proxy_type'].upper()
            self.curl.setopt(pycurl.PROXYTYPE, getattr(pycurl, key))

        if grab.config['encoding']:
            if ('gzip' in grab.config['encoding'] and
                    'zlib' not in pycurl.version):
                raise error.GrabMisuseError(
                    'You can not use gzip encoding because '
                    'pycurl was built without zlib support')
            self.curl.setopt(pycurl.ENCODING, grab.config['encoding'])

        if grab.config['userpwd']:
            self.curl.setopt(pycurl.USERPWD, str(grab.config['userpwd']))

        if grab.config.get('interface') is not None:
            self.curl.setopt(pycurl.INTERFACE, grab.config['interface'])

        if grab.config.get('reject_file_size') is not None:
            self.curl.setopt(pycurl.MAXFILESIZE,
                             grab.config['reject_file_size'])

    def process_cookie_options(self, grab, request_url):
        request_host = urlsplit(request_url).netloc.split(':')[0]
        if request_host.startswith('www.'):
            request_host_no_www = request_host[4:]
        else:
            request_host_no_www = request_host

        # `cookiefile` option should be processed before `cookies` option
        # because `load_cookies` updates `cookies` option
        if grab.config['cookiefile']:
            # Do not raise exception if cookie file does not exist
            try:
                grab.cookies.load_from_file(grab.config['cookiefile'])
            except IOError as ex:
                logging.error(ex)

        # Process `cookies` option that is simple dict i.e.
        # it provides only `name` and `value` attributes of cookie
        # No domain, no path, no expires, etc
        # I pass these no-domain cookies to *each* requested domain
        # by setting these cookies with corresponding domain attribute
        # Trying to guess better domain name by removing leading "www."
        if grab.config['cookies']:
            if not isinstance(grab.config['cookies'], dict):
                raise error.GrabMisuseError('cookies option should be a dict')
            for name, value in grab.config['cookies'].items():
                grab.cookies.set(
                    name=name,
                    value=value,
                    domain=request_host_no_www
                )

        # Erase known cookies stored in pycurl handler
        self.curl.setopt(pycurl.COOKIELIST, 'ALL')

        # Enable pycurl cookie processing mode
        self.curl.setopt(pycurl.COOKIELIST, '')

        # Put all cookies from `grab.cookies.cookiejar` to
        # the pycurl instance.
        # We put *all* cookies, for all host names
        # Pycurl cookie engine is smart enough to send
        # only cookies belong to the current request's host name
        for cookie in grab.cookies.cookiejar:
            self.curl.setopt(pycurl.COOKIELIST,
                             self.get_netscape_cookie_spec(cookie,
                                                           request_host))

    def get_netscape_cookie_spec(self, cookie, request_host):
        # FIXME: Now cookie.domain could not be None
        # request_host is not needed anymore
        host = cookie.domain or request_host
        if cookie.get_nonstandard_attr('HttpOnly'):
            host = '#HttpOnly_' + host
        items = [
            host,
            'TRUE',
            cookie.path,
            'TRUE' if cookie.secure else 'FALSE',
            str(cookie.expires) if cookie.expires\
                else 'Fri, 31 Dec 9999 23:59:59 GMT',
            cookie.name,
            cookie.value,
        ]
        out = u'\t'.join(items)
        return out

    def request(self):

        try:
            self.curl.perform()
        except pycurl.error as ex:
            # CURLE_WRITE_ERROR (23)
            # An error occurred when writing received data to a local file, or
            # an error was returned to libcurl from a write callback.
            # This exception should be ignored if _callback_interrupted flag
            # is enabled (this happens when nohead or nobody options enabled)
            #
            # Also this error is raised when curl receives KeyboardInterrupt
            # while it is processing some callback function
            # (WRITEFUNCTION, HEADERFUNCTIO, etc)
            if 23 == ex.args[0]:
                if getattr(self.curl, '_callback_interrupted', None) is True:
                    self.curl._callback_interrupted = False
                else:
                    raise error.GrabNetworkError(ex.args[0], ex.args[1])
            else:
                if ex.args[0] == 28:
                    raise error.GrabTimeoutError(ex.args[0], ex.args[1])
                elif ex.args[0] == 7:
                    raise error.GrabConnectionError(ex.args[0], ex.args[1])
                elif ex.args[0] == 67:
                    raise error.GrabAuthError(ex.args[0], ex.args[1])
                elif ex.args[0] == 47:
                    raise error.GrabTooManyRedirectsError(ex.args[0],
                                                          ex.args[1])
                elif ex.args[0] == 6:
                    raise error.GrabCouldNotResolveHostError(ex.args[0],
                                                             ex.args[1])
                else:
                    raise error.GrabNetworkError(ex.args[0], ex.args[1])
        except Exception as ex:
            six.reraise(error.GrabInternalError, error.GrabInternalError(ex),
                        sys.exc_info()[2])

    def prepare_response(self, grab):
        if self.body_file:
            self.body_file.close()
        response = Response()

        response.head = b''.join(self.response_header_chunks)

        if self.body_path:
            response.body_path = self.body_path
        else:
            response.body = b''.join(self.response_body_chunks)

        # Clear memory
        self.response_header_chunks = []
        self.response_body_chunks = []

        response.code = self.curl.getinfo(pycurl.HTTP_CODE)
        response.total_time = self.curl.getinfo(pycurl.TOTAL_TIME)
        response.connect_time = self.curl.getinfo(pycurl.CONNECT_TIME)
        response.name_lookup_time = self.curl.getinfo(pycurl.NAMELOOKUP_TIME)
        response.download_size = self.curl.getinfo(pycurl.SIZE_DOWNLOAD)
        response.upload_size = self.curl.getinfo(pycurl.SIZE_UPLOAD)
        response.download_speed = self.curl.getinfo(pycurl.SPEED_DOWNLOAD)
        response.remote_ip = self.curl.getinfo(pycurl.PRIMARY_IP)

        response.url = self.curl.getinfo(pycurl.EFFECTIVE_URL)

        response.parse(charset=grab.config['document_charset'])

        response.cookies = CookieManager(self.extract_cookiejar())

        # We do not need anymore cookies stored in the
        # curl instance so drop them
        self.curl.setopt(pycurl.COOKIELIST, 'ALL')
        return response

    def extract_cookiejar(self):
        """
        Extract cookies that pycurl instance knows.

        Returns `CookieJar` object.
        """

        # Example of line:
        # www.google.com\tFALSE\t/accounts/\tFALSE\t0'
        # \tGoogleAccountsLocale_session\ten
        # Fields:
        # * domain
        # * whether or not all machines under that domain can
        # read the cookie's information.
        # * path
        # * Secure Flag: whether or not a secure connection (HTTPS)
        # is required to read the cookie.
        # * exp. timestamp
        # * name
        # * value
        cookiejar = CookieJar()
        for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            values = line.split('\t')
            domain = values[0].lower()
            if domain.startswith('#httponly_'):
                domain = domain.replace('#httponly_', '')
                httponly = True
            else:
                httponly = False
            # old
            # cookies[values[-2]] = values[-1]
            # new
            cookie = create_cookie(
                name=values[5],
                value=values[6],
                domain=domain,
                path=values[2],
                secure=values[3] == "TRUE",
                expires=int(values[4]) if values[4] else None,
                httponly=httponly,
            )
            cookiejar.set_cookie(cookie)
        return cookiejar

    def __getstate__(self):
        """
        Reset curl attribute which could not be pickled.
        """
        state = self.__dict__.copy()
        state['curl'] = None
        return state

    def __setstate__(self, state):
        """
        Create pycurl instance after Grab instance was restored
        from pickled state.
        """

        state['curl'] = pycurl.Curl()
        self.__dict__ = state


# from grab.base import BaseGrab
# class GrabCurl(CurlTransportExtension, BaseGrab):
    # pass
