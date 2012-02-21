# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
import email
import logging
import urllib
from StringIO import StringIO
import threading
import random

from ..base import (GrabError, GrabMisuseError, UploadContent, UploadFile,
                    GrabTimeoutError, GrabNetworkError)

logger = logging.getLogger('grab')

# @lorien: I do not understand these signals. Maybe you?

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.

# http://curl.haxx.se/mail/curlpython-2005-06/0004.html
# http://curl.haxx.se/mail/lib-2010-03/0114.html

#CURLOPT_NOSIGNAL
#Pass a long. If it is 1, libcurl will not use any functions that install
# signal handlers or any functions that cause signals to be sent to the
# process. This option is mainly here to allow multi-threaded unix applications
# to still set/use all timeout options etc, without risking getting signals.
# (Added in 7.10)

#If this option is set and libcurl has been built with the standard name
# resolver, timeouts will not occur while the name resolve takes place.
# Consider building libcurl with c-ares support to enable asynchronous DNS 
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


class CurlTransportExtension(object):
    def extra_init(self):
        import pycurl

        self.curl = pycurl.Curl()

    def extra_reset(self):
        self.response_head_chunks = []
        self.response_body_chunks = []
        self.response_body_bytes_read = 0
        self.request_headers = ''
        self.request_head = ''
        self.request_log = ''
        self.request_body = ''
        self.request_method = None

    def head_processor(self, chunk):
        """
        Process head of response.
        """

        #if self.config['nohead']:
            #return 0
        self.response_head_chunks.append(chunk)
        # Returning None implies that all bytes were written
        return None

    def body_processor(self, chunk):
        """
        Process body of response.
        """

        if self.config['nobody']:
            return 0

        bytes_read = len(chunk)
        self.response_body_bytes_read += bytes_read
        self.response_body_chunks.append(chunk)
        if self.config['body_maxsize'] is not None:
            if self.response_body_bytes_read > self.config['body_maxsize']:
                logging.debug('Response body max size limit reached: %s' %
                              self.config['body_maxsize'])
                return 0

        # Returning None implies that all bytes were written
        return None

    def debug_processor(self, _type, text):
        """
        Parse request headers and save to ``self.request_headers``

        0: CURLINFO_TEXT
        1: CURLINFO_HEADER_IN
        2: CURLINFO_HEADER_OUT
        3: CURLINFO_DATA_IN
        4: CURLINFO_DATA_OUT
        5: CURLINFO_unrecognized_type
        """
        import pycurl

        if _type == pycurl.INFOTYPE_HEADER_OUT:
            self.request_head += text
            lines = text.splitlines()
            text = '\n'.join(lines[1:])
            self.request_headers = email.message_from_string(text)

        if _type == pycurl.INFOTYPE_DATA_OUT:
            self.request_body += text

        if _type == pycurl.INFOTYPE_TEXT:
            if self.request_log is None:
                self.request_log = ''
            self.request_log += text

    def process_config(self):
        """
        Setup curl instance with values from ``self.config``.
        """
        import pycurl

        url = self.config['url']
        if isinstance(url, unicode):
            url = url.encode('utf-8')
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])
        self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        self.curl.setopt(pycurl.NOSIGNAL, 1)
        self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)

        # User-Agent
        if self.config['user_agent'] is None:
            if self.config['user_agent_file'] is not None:
                with open(self.config['user_agent_file']) as inf:
                    lines = inf.read().splitlines()
                self.config['user_agent'] = random.choice(lines)

        # If value is None then set empty string
        # None is not acceptable because in such case
        # pycurl will set its default user agent "PycURL/x.xx.x"
        if not self.config['user_agent']:
            self.config['user_agent'] = ''

        self.curl.setopt(pycurl.USERAGENT, self.config['user_agent'])

        self.curl.setopt(pycurl.VERBOSE, 1)
        self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        # Ignore SSL errors
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        if self.request_method == 'POST':
            self.curl.setopt(pycurl.POST, 1)
            if self.config['multipart_post']:
                if isinstance(self.config['multipart_post'], basestring):
                    raise GrabMisuseError('multipart_post option could not be a string')
                post_items = self.normalize_http_values(self.config['multipart_post'])
                self.curl.setopt(pycurl.HTTPPOST, post_items) 
            elif self.config['post']:
                if isinstance(self.config['post'], basestring):
                    # bytes-string should be posted as-is
                    # unicode should be converted into byte-string
                    if isinstance(self.config['post'], unicode):
                        post_data = self.normalize_unicode(self.config['post'])
                    else:
                        post_data = self.config['post']
                else:
                    # dict, tuple, list should be serialized into byte-string
                    post_data = self.urlencode(self.config['post'])
                self.curl.setopt(pycurl.POSTFIELDS, post_data)
        elif self.request_method == 'PUT':
            self.curl.setopt(pycurl.PUT, 1)
            self.curl.setopt(pycurl.READFUNCTION, StringIO(self.config['post']).read) 
        elif self.request_method == 'DELETE':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        elif self.request_method == 'HEAD':
            self.curl.setopt(pycurl.NOBODY, 1)
        else:
            self.curl.setopt(pycurl.HTTPGET, 1)
        
        headers = self.default_headers
        if self.config['headers']:
            headers.update(self.config['headers'])
        header_tuples = [str('%s: %s' % x) for x\
                         in headers.iteritems()]
        self.curl.setopt(pycurl.HTTPHEADER, header_tuples)


        # CURLOPT_COOKIELIST
        # Pass a char * to a cookie string. Cookie can be either in
        # Netscape / Mozilla format or just regular HTTP-style
        # header (Set-Cookie: ...) format.
        # If cURL cookie engine was not enabled it will enable its cookie
        # engine.
        # Passing a magic string "ALL" will erase all cookies known by cURL.
        # (Added in 7.14.1)
        # Passing the special string "SESS" will only erase all session
        # cookies known by cURL. (Added in 7.15.4)
        # Passing the special string "FLUSH" will write all cookies known by
        # cURL to the file specified by CURLOPT_COOKIEJAR. (Added in 7.17.1)

        # CURLOPT_COOKIE
        # Pass a pointer to a zero terminated string as parameter. It will be used to set a cookie in the http request. The format of the string should be NAME=CONTENTS, where NAME is the cookie name and CONTENTS is what the cookie should contain.
        # If you need to set multiple cookies, you need to set them all using a single option and thus you need to concatenate them all in one single string. Set multiple cookies in one string like this: "name1=content1; name2=content2;" etc.
        # Note that this option sets the cookie header explictly in the outgoing request(s). If multiple requests are done due to authentication, followed redirections or similar, they will all get this cookie passed on.
        # Using this option multiple times will only make the latest string override the previous ones. 

        if self.config['cookies']:
            items = self.encode_cookies(self.config['cookies'], join=False)
            self.curl.setopt(pycurl.COOKIELIST, 'ALL')
            for item in items:
                self.curl.setopt(pycurl.COOKIELIST, 'Set-Cookie: %s' % item)
        else:
            # Turn on cookies engine anyway
            # To correctly support cookies in 302-redirects
            self.curl.setopt(pycurl.COOKIELIST, '')

        #if not self.config['reuse_cookies'] and not self.config['cookies']:
            #self.curl.setopt(pycurl.COOKIELIST, 'ALL')

        if self.config['cookiefile']:
            self.load_cookies(self.config['cookiefile'])

        if self.config['referer']:
            self.curl.setopt(pycurl.REFERER, str(self.config['referer']))

        if self.config['proxy']:
            self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 
        else:
            self.curl.setopt(pycurl.PROXY, '')

        if self.config['proxy_userpwd']:
            self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])

        # PROXYTYPE
        # Pass a long with this option to set type of the proxy. Available options for this are CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4), CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5, CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0). The HTTP type is default. (Added in 7.10) 

        if self.config['proxy_type']:
            ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
            self.curl.setopt(pycurl.PROXYTYPE, ptype)

        if self.config['encoding']:
            if 'gzip' in self.config['encoding'] and not 'zlib' in pycurl.version:
                raise GrabMisuseError('You can not use gzip encoding because '\
                                      'pycurl was built without zlib support')
            self.curl.setopt(pycurl.ENCODING, self.config['encoding'])

        if self.config['userpwd']:
            self.curl.setopt(pycurl.USERPWD, self.config['userpwd'])

        if self.config['charset']:
            self.charset = self.config['charset']

    def transport_request(self):
        import pycurl

        try:
            self.curl.perform()
        except pycurl.error, ex:
            # CURLE_WRITE_ERROR
            # An error occurred when writing received data to a local file, or
            # an error was returned to libcurl from a write callback.
            # This is expected error and we should ignore it
            if 23 == ex[0]:
                pass
            else:
                if ex[0] == 28:
                    raise GrabTimeoutError(ex[0], ex[1])
                else:
                    raise GrabNetworkError(ex[0], ex[1])

    def prepare_response(self):
        import pycurl

        self.response.head = ''.join(self.response_head_chunks)
        self.response.body = ''.join(self.response_body_chunks)
        self.response.code = self.curl.getinfo(pycurl.HTTP_CODE)
        self.response.time = self.curl.getinfo(pycurl.TOTAL_TIME)
        self.response.url = self.curl.getinfo(pycurl.EFFECTIVE_URL)

        if self.config['charset'] is not None:
            self.response.parse(charset=self.config['charset'])
        else:
            self.response.parse()

        self.response.cookies = self.extract_cookies()

        # We do not need anymore cookies stored in the
        # curl instance so drop them
        self.curl.setopt(pycurl.COOKIELIST, 'ALL')

    # TODO: move to base
    def load_cookies(self, path):
        """
        Load cookies from the file.

        The cookie data may be in Netscape / Mozilla cookie data format or just regular HTTP-style headers dumped to a file.
        """
        import pycurl

        self.curl.setopt(pycurl.COOKIEFILE, path)


    # TODO: move to base
    def dump_cookies(self, path):
        """
        Dump all cookies to file.

        Each cookie is dumped in the format:
        # www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        """
        import pycurl

        with open(path, 'w') as out:
            out.write('\n'.join(self.curl.getinfo(pycurl.INFO_COOKIELIST)))

    def clear_cookies(self):
        """
        Clear all cookies.

        Custom version of BaseCurl.clear_cookies which do additional action:
        reset cookies in curl instance.
        """
        import pycurl

        self.config['cookies'] = {}
        self.curl.setopt(pycurl.COOKIELIST, 'ALL')

    def extract_cookies(self):
        """
        Extract cookies.
        """
        import pycurl

        # Example of line:
        # www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        cookies = {}
        for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            chunks = line.split('\t')
            cookies[chunks[-2]] = chunks[-1]
        return cookies



from ..base import BaseGrab
class GrabCurl(CurlTransportExtension, BaseGrab):
    pass
