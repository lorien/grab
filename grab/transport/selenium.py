# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
import email
import logging
#import urllib
#try:
#    from StringIO import StringIO
#except ImportError:
#    from io import StringIO
import threading
import random
import time
import os
import json

from ..response import Response
from ..error import GrabError, GrabMisuseError
from ..base import UploadContent, UploadFile

from grab.util.py3k_support import *

logger = logging.getLogger('grab')


"""
dir(self.browser)

['__class__',
 '__delattr__',
 '__dict__',
 '__doc__',
 '__format__',
 '__getattribute__',
 '__hash__',
 '__init__',
 '__module__',
 '__new__',
 '__reduce__',
 '__reduce_ex__',
 '__repr__',
 '__setattr__',
 '__sizeof__',
 '__str__',
 '__subclasshook__',
 '__weakref__',
 '_unwrap_value',
 '_wrap_value',
 'add_cookie',
 'back',
 'binary',
 'capabilities',
 'close',
 'command_executor',
 'create_web_element',
 'current_url',
 'current_window_handle',
 'delete_all_cookies',
 'delete_cookie',
 'desired_capabilities',
 'error_handler',
 'execute',
 'execute_async_script',
 'execute_script',
 'find_element',
 'find_element_by_class_name',
 'find_element_by_css_selector',
 'find_element_by_id',
 'find_element_by_link_text',
 'find_element_by_name',
 'find_element_by_partial_link_text',
 'find_element_by_tag_name',
 'find_element_by_xpath',
 'find_elements',
 'find_elements_by_class_name',
 'find_elements_by_css_selector',
 'find_elements_by_id',
 'find_elements_by_link_text',
 'find_elements_by_name',
 'find_elements_by_partial_link_text',
 'find_elements_by_tag_name',
 'find_elements_by_xpath',
 'firefox_profile',
 'forward',
 'get',
 'get_cookie',
 'get_cookies',
 'get_screenshot_as_base64',
 'get_screenshot_as_file',
 'get_window_position',
 'get_window_size',
 'implicitly_wait',
 'name',
 'orientation',
 'page_source',
 'profile',
 'quit',
 'refresh',
 'save_screenshot',
 'session_id',
 'set_script_timeout',
 'set_window_position',
 'set_window_size',
 'start_client',
 'start_session',
 'stop_client',
 'switch_to_active_element',
 'switch_to_alert',
 'switch_to_default_content',
 'switch_to_frame',
 'switch_to_window',
 'title',
 'window_handles']
"""


class SeleniumTransportExtension(object):
    def extra_config(self):
        self.config['xserver_display'] = 0

    #def extra_init(self):
        #pass

    #def extra_reset(self):
        #self.response_head_chunks = []
        #self.response_body_chunks = []
        #self.request_headers = ''
        #self.request_head = ''
        #self.request_log = ''
        #self.request_body = ''

    #def head_processor(self, chunk):
        #"""
        #Process head of response.
        #"""

        #if self.config['nohead']:
            #return 0
        #self.response_head_chunks.append(chunk)
        ## Returning None implies that all bytes were written
        #return None

    #def body_processor(self, chunk):
        #"""
        #Process body of response.
        #"""

        #if self.config['nobody']:
            #return 0
        #self.response_body_chunks.append(chunk)
        ## Returning None implies that all bytes were written
        #return None

    #def debug_processor(self, _type, text):
        #"""
        #Parse request headers and save to ``self.request_headers``

        #0: CURLINFO_TEXT
        #1: CURLINFO_HEADER_IN
        #2: CURLINFO_HEADER_OUT
        #3: CURLINFO_DATA_IN
        #4: CURLINFO_DATA_OUT
        #5: CURLINFO_unrecognized_type
        #"""

        #if _type == pycurl.INFOTYPE_HEADER_OUT:
            #self.request_head += text
            #lines = text.splitlines()
            #text = '\n'.join(lines[1:])
            #self.request_headers = dict(email.message_from_string(text))

        #if _type == pycurl.INFOTYPE_DATA_OUT:
            #self.request_body += text

        #if _type == pycurl.INFOTYPE_TEXT:
            #if self.request_log is None:
                #self.request_log = ''
            #self.request_log += text

    def process_config(self, grab):
        """
        Setup curl instance with values from ``self.config``.
        """

        from selenium import webdriver

        display = ':%s.0' % grab.config.get('xserver_display')
        logging.debug('Setting DISPLAY env to %s' % display)
        os.environ['DISPLAY'] = display

        driver = grab.config.get('webdriver', 'firefox')

        if driver.lower() == 'chrome':
            self.browser = webdriver.Chrome()
        elif driver.lower() == 'opera':
            self.browser = webdriver.Opera()
        elif driver.lower() == 'ie':
            self.browser = webdriver.Ie()
        else:
            self.browser = webdriver.Firefox()

        if grab.config['method']:
            method = grab.config['method'].lower()
        else:
            method = 'get'

        self.config = {
            'url': grab.config['url'],
            'wait': grab.config['selenium_wait'],
            'method': method,
            'post': grab.config.get('post', {})
        }

        #url = self.config['url']
        if isinstance(grab.config['url'], unicode):
            #url = url.encode('utf-8')
            grab.config['url'] = grab.config['url'].encode('utf-8')

        #self.curl.setopt(pycurl.URL, url)
        #self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        #self.curl.setopt(pycurl.MAXREDIRS, 5)
        #self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])
        #self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        #self.curl.setopt(pycurl.NOSIGNAL, 1)
        #self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        #self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)

        ## User-Agent
        #if self.config['user_agent'] is None:
            #if self.config['user_agent_file'] is not None:
                #lines = open(self.config['user_agent_file']).read().splitlines()
                #self.config['user_agent'] = random.choice(lines)

        ## If value is None then set empty string
        ## None is not acceptable because in such case
        ## pycurl will set its default user agent "PycURL/x.xx.x"
        #if not self.config['user_agent']:
            #self.config['user_agent'] = ''

        #self.curl.setopt(pycurl.USERAGENT, self.config['user_agent'])

        #if self.config['debug']:
            #self.curl.setopt(pycurl.VERBOSE, 1)
            #self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        ## Ignore SSL errors
        #self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        #self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        #method = self.config['method']
        #if method:
            #method = method.upper()
        #else:
            #if self.config['post'] or self.config['multipart_post']:
                #method = 'POST'
            #else:
                #method = 'GET'

        #if method == 'POST':
            #self.curl.setopt(pycurl.POST, 1)
            #if self.config['multipart_post']:
                #if not isinstance(self.config['multipart_post'], (list, tuple)):
                    #raise GrabMisuseError('multipart_post should be tuple or list, not dict')
                #post_items = self.normalize_http_values(self.config['multipart_post'], charset=self.charset)
                #self.curl.setopt(pycurl.HTTPPOST, post_items) 
            #elif self.config['post']:
                #if isinstance(self.config['post'], basestring):
                    ## bytes-string should be posted as-is
                    ## unicode should be converted into byte-string
                    #if isinstance(self.config['post'], unicode):
                        #post_data = self.normalize_unicode(self.config['post'])
                    #else:
                        #post_data = self.config['post']
                #else:
                    ## dict, tuple, list should be serialized into byte-string
                    #post_data = self.urlencode(self.config['post'])
                #self.curl.setopt(pycurl.POSTFIELDS, post_data)
        #elif method == 'PUT':
            #self.curl.setopt(pycurl.PUT, 1)
            #self.curl.setopt(pycurl.READFUNCTION, StringIO(self.config['post']).read) 
        #elif method == 'DELETE':
            #self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        #elif method == 'HEAD':
            #self.curl.setopt(pycurl.NOBODY, 1)
        #else:
            #self.curl.setopt(pycurl.HTTPGET, 1)
        
        #headers = self.config['common_headers']
        #if self.config['headers']:
            #headers.update(self.config['headers'])
        #header_tuples = [str('%s: %s' % x) for x\
                         #in headers.iteritems()]
        #self.curl.setopt(pycurl.HTTPHEADER, header_tuples)


        ## CURLOPT_COOKIELIST
        ## Pass a char * to a cookie string. Cookie can be either in
        ## Netscape / Mozilla format or just regular HTTP-style
        ## header (Set-Cookie: ...) format.
        ## If cURL cookie engine was not enabled it will enable its cookie
        ## engine.
        ## Passing a magic string "ALL" will erase all cookies known by cURL.
        ## (Added in 7.14.1)
        ## Passing the special string "SESS" will only erase all session
        ## cookies known by cURL. (Added in 7.15.4)
        ## Passing the special string "FLUSH" will write all cookies known by
        ## cURL to the file specified by CURLOPT_COOKIEJAR. (Added in 7.17.1)

        #if self.config['reuse_cookies']:
            ## Setting empty string will activate curl cookie engine
            #self.curl.setopt(pycurl.COOKIELIST, '')
        #else:
            #self.curl.setopt(pycurl.COOKIELIST, 'ALL')


        ## CURLOPT_COOKIE
        ## Pass a pointer to a zero terminated string as parameter. It will be used to set a cookie in the http request. The format of the string should be NAME=CONTENTS, where NAME is the cookie name and CONTENTS is what the cookie should contain.
        ## If you need to set multiple cookies, you need to set them all using a single option and thus you need to concatenate them all in one single string. Set multiple cookies in one string like this: "name1=content1; name2=content2;" etc.
        ## Note that this option sets the cookie header explictly in the outgoing request(s). If multiple requests are done due to authentication, followed redirections or similar, they will all get this cookie passed on.
        ## Using this option multiple times will only make the latest string override the previous ones. 

        #if self.config['cookies']:
            #self.curl.setopt(pycurl.COOKIE, self.encode_cookies(self.config['cookies']))

        #if self.config['cookiefile']:
            #self.load_cookies(self.config['cookiefile'])

        #if self.config['referer']:
            #self.curl.setopt(pycurl.REFERER, str(self.config['referer']))

        #if self.config['proxy']:
            #self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 
        #else:
            #self.curl.setopt(pycurl.PROXY, '')

        #if self.config['proxy_userpwd']:
            #self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])

        ## PROXYTYPE
        ## Pass a long with this option to set type of the proxy. Available options for this are CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4), CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5, CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0). The HTTP type is default. (Added in 7.10) 

        #if self.config['proxy_type']:
            #ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
            #self.curl.setopt(pycurl.PROXYTYPE, ptype)

        #if self.config['proxy']:
            #if self.config['proxy_userpwd']:
                #auth = ' with authorization'
            #else:
                #auth = ''
            #proxy_info = ' via %s proxy of type %s%s' % (
                #self.config['proxy'], self.config['proxy_type'], auth)
        #else:
            #proxy_info = ''

        #tname = threading.currentThread().getName().lower()
        #if tname == 'mainthread':
            #tname = ''
        #else:
            #tname = '-%s' % tname

        #logger.debug('[%02d%s] %s %s%s' % (self.request_counter, tname, method, self.config['url'], proxy_info))

        #if self.config['encoding']:
            #self.curl.setopt(pycurl.ENCODING, self.config['encoding'])

        #if self.config['userpwd']:
            #self.curl.setopt(pycurl.USERPWD, self.config['userpwd'])

        #if self.config['charset']:
            #self.charset = self.config['charset']

    def _extract_cookies(self):
        """
        Extract cookies.
        """

        # Example of line:
        # www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        #cookies = {}
        #for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            #chunks = line.split('\t')
            #cookies[chunks[-2]] = chunks[-1]
        #return cookies
        cookies = {}
        for item in self.browser.get_cookies():
            cookies[item['name']] = item['value']
        return cookies

    def request(self):
        try:
            if self.config['method'] == 'post':
                post_params = json.dumps(self.config['post'])
                script = """
                    var form = document.createElement("form");
                    form.setAttribute("method", "POST");
                    form.setAttribute("action", "%s");

                    var params = %s;

                    for(var key in params) {
                        if(params.hasOwnProperty(key)) {
                            var hiddenField = document.createElement("input");
                            hiddenField.setAttribute("type", "hidden");
                            hiddenField.setAttribute("name", key);
                            hiddenField.setAttribute("value", params[key]);

                            form.appendChild(hiddenField);
                         }
                    }

                    document.body.appendChild(form);
                    form.submit();
                """ % (self.config['url'], post_params)

                self.browser.execute_script(script)
            else:
                self.browser.get(self.config['url'])
                time.sleep(self.config['wait'])
        except Exception as ex:
            logging.error('', exc_info=ex)
            raise GrabError(999, 'Error =8-[ ]')
        #try:
            #self.curl.perform()
        #except pycurl.error, ex:
            ## CURLE_WRITE_ERROR
            ## An error occurred when writing received data to a local file, or
            ## an error was returned to libcurl from a write callback.
            ## This is expected error and we should ignore it
            #if 23 == ex[0]:
                #pass
            #else:
                #raise GrabError(ex[0], ex[1])

    def prepare_response(self, grab):
        #self.response.head = ''.join(self.response_head_chunks)
        #self.response.body = ''.join(self.response_body_chunks)
        #self.response.parse()

        response = Response()

        response.head = ''
        response._unicode_body = self.browser.page_source
        response.body = self.browser.page_source.encode('utf-8')
        response.charset = 'utf-8'
        #import pdb; pdb.set_trace()
        response.url = self.browser.current_url
        response.code = 200# TODO: fix, self.browser.status_code
        response.cookies = self._extract_cookies()
        #self.response.code = self.curl.getinfo(pycurl.HTTP_CODE)
        #self.response.time = self.curl.getinfo(pycurl.TOTAL_TIME)
        #self.response.url = self.curl.getinfo(pycurl.EFFECTIVE_URL)
        #import pdb; pdb.set_trace()
        self.browser.quit()

        return response

    def reset(self):
        # Maybe move to super-class???
        self.request_head = ''
        self.request_body = ''
        self.request_log = ''

    #def load_cookies(self, path):
        #"""
        #Load cookies from the file.

        #The cookie data may be in Netscape / Mozilla cookie data format or just regular HTTP-style headers dumped to a file.
        #"""

        #self.curl.setopt(pycurl.COOKIEFILE, path)


    #def dump_cookies(self, path):
        #"""
        #Dump all cookies to file.

        #Each cookie is dumped in the format:
        ## www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        #"""

        #open(path, 'w').write('\n'.join(self.curl.getinfo(pycurl.INFO_COOKIELIST)))

    #def clear_cookies(self):
        #"""
        #Clear all cookies.
        #"""

        ## Write tests
        #self.curl.setopt(pycurl.COOKIELIST, 'ALL')
        #self.config['cookies'] = {}
        #self.response.cookies = None

    #def reset_curl_instance(self):
        #"""
        #Completely recreate curl instance from scratch.
        
        #I add this method because I am not sure that
        #``clear_cookies`` method works fine and I should be sure
        #I can reset all cokies.
        #"""

        #self.curl = pycurl.Curl()


# from ..base import BaseGrab
# class GrabSelenium(SeleniumTransportExtension, BaseGrab):
#     def __init__(self, response_body=None):
#         super(GrabSelenium, self).__init__(response_body, 'selenium.SeleniumTransportExtension')
