# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
import logging
import urllib2
import cookielib
import socket

from ..base import GrabError

logger = logging.getLogger('grab')

class Extension(object):
    def extra_init(self):
        cj = cookielib.CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),
                                            urllib2.HTTPSHandler())
        #self._referer = None
        #self.headers = headers.random_request()

    def extra_reset(self):
        self._post_data = None

    def process_config(self):
        url = self.config['url']
        if isinstance(url, unicode):
            url = url.encode('utf-8')
            
        #self.curl.setopt(pycurl.URL, url)
        req = urllib2.Request(url)

        #self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        #self.curl.setopt(pycurl.MAXREDIRS, 5)
        #self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])

        #self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        socket.setdefaulttimeout(self.config['timeout'])

        #self.curl.setopt(pycurl.NOSIGNAL, 1)
        #self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        #self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)
        #self.curl.setopt(pycurl.USERAGENT, self.config['user_agent'])

        #if self.config['debug']:
            #self.curl.setopt(pycurl.VERBOSE, 1)
            #self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        # Ignore SSL errors
        #self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        #self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        method = self.config['method']
        if method:
            method = method.upper()
        else:
            if self.config['payload'] or self.config['post']:
                method = 'POST'
            else:
                method = 'GET'

        post_data = None
        if method == 'POST':
            #self.curl.setopt(pycurl.POST, 1)
            #if self.config['payload']:
                #self.curl.setopt(pycurl.POSTFIELDS, self.config['payload'])
            #elif self.config['post']:
            if self.config['post']:
                self._post_data = self.urlencode(self.config['post'])
                #self.curl.setopt(pycurl.POSTFIELDS, post_data)
        #elif method == 'PUT':
            #self.curl.setopt(pycurl.PUT, 1)
            #self.curl.setopt(pycurl.READFUNCTION, StringIO(self.config['payload']).read) 
        #elif method == 'DELETE':
            #self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        else:
            #self.curl.setopt(pycurl.HTTPGET, 1)
            pass

        # TODO: start fucking from here in next time...
        
        headers = self.default_headers
        if self.config['headers']:
            headers.update(self.config['headers'])
        for key, value in headers.iteritems():
            req.add_header(key, value)
        #headers_tuples = [str('%s: %s' % x) for x\
                          #in self.config['headers'].iteritems()]
        #self.curl.setopt(pycurl.HTTPHEADER, headers_tuples)


        # CURLOPT_COOKIELIST
        # Pass a char * to a cookie string. Cookie can be either in Netscape / Mozilla format or just regular HTTP-style header (Set-Cookie: ...) format.
        # If cURL cookie engine was not enabled it will enable its cookie engine.
        # Passing a magic string "ALL" will erase all cookies known by cURL. (Added in 7.14.1)
        # Passing the special string "SESS" will only erase all session cookies known by cURL. (Added in 7.15.4)
        # Passing the special string "FLUSH" will write all cookies known by cURL to the file specified by CURLOPT_COOKIEJAR. (Added in 7.17.1)

        #if self.config['reuse_cookies']:
            ## Setting empty string will activate curl cookie engine
            #self.curl.setopt(pycurl.COOKIELIST, '')
        #else:
            #self.curl.setopt(pycurl.COOKIELIST, 'ALL')


        # CURLOPT_COOKIE
        # Pass a pointer to a zero terminated string as parameter. It will be used to set a cookie in the http request. The format of the string should be NAME=CONTENTS, where NAME is the cookie name and CONTENTS is what the cookie should contain.
        # If you need to set multiple cookies, you need to set them all using a single option and thus you need to concatenate them all in one single string. Set multiple cookies in one string like this: "name1=content1; name2=content2;" etc.
        # Note that this option sets the cookie header explictly in the outgoing request(s). If multiple requests are done due to authentication, followed redirections or similar, they will all get this cookie passed on.
        # Using this option multiple times will only make the latest string override the previous ones. 

        #if self.config['cookies']:
            #chunks = []
            #for key, value in self.config['cookies'].iteritems():
                #key = urllib.quote_plus(key)
                #value = urllib.quote_plus(value)
                #chunks.append('%s=%s;' % (key, value))
            #self.curl.setopt(pycurl.COOKIE, ''.join(chunks))

        if self.config['referer']:
            #self.curl.setopt(pycurl.REFERER, str(self.config['referer']))
            req.add_header('Referer', str(self.config['referer']))

        if self.config['proxy']:
            #self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 
            req.set_proxy(str(self.config['proxy']))

        #if self.config['proxy_userpwd']:
            #self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])

        # PROXYTYPE
        # Pass a long with this option to set type of the proxy. Available options for this are CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4), CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5, CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0). The HTTP type is default. (Added in 7.10) 

        #if self.config['proxy_type']:
            #ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
            #self.curl.setopt(pycurl.PROXYTYPE, ptype)

        if self.config['proxy']:
            #if self.config['proxy_userpwd']:
                #auth = ' with authorization'
            #else:
                #auth = ''
            auth = ''
            proxy_info = ' via %s proxy of type %s%s' % (
                self.config['proxy'], self.config['proxy_type'], auth)
        else:
            proxy_info = ''

        logger.debug('[%02d] %s %s%s' % (self.request_counter, method, self.config['url'], proxy_info))
        self.req = req

    def extract_cookies(self):
        """
        Extract cookies.
        """

        return {}

    def request(self):
        try:
            self._resp = self._opener.open(self.req)
            self._resp_body = self._resp.read()
        except urllib2.URLError:
            raise GrabError(ex[0], ex[1])

    def prepare_response(self):
        self.response.body = self._resp_body
        self.response.headers = dict(self._resp.headers)
        #self.response.head = ''.join(self.response_head_chunks)
        #self.response.body = ''.join(self.response_body_chunks)
        #self.response.parse()
        #self.response.cookies = self.extract_cookies()
        #self.response.time = self.curl.getinfo(pycurl.TOTAL_TIME)
        self.response.code = self._resp.code
        self.response.url = self._resp.geturl()


