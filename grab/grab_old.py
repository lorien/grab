# -*- coding: utf-8 -*-
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import pycurl
from StringIO import StringIO
import logging
import os
import urllib
import re
from random import randint, choice
from copy import deepcopy, copy
import threading
from urlparse import urljoin
import email

from html import make_unicode, find_refresh_url
import user_agent

log = logging.getLogger('grab')
#__all__ = ['Grab', 'request']

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    # Ignore error in python 2.5
    except ValueError:
        pass
except ImportError:
    pass

class GrabError(pycurl.error):
    pass

class DataNotFound(Exception):
    pass

SCRIPT_TAG = re.compile(r'(<script[^>]*>).+?(</script>)', re.I|re.S)


def request(url, **kwargs):
    """
    Shortcut for single request.
    """

    grab = Grab()
    grab.setup(url=url, **kwargs)
    grab.request()
    return {'body': grab.response_body,
            'headers': grab.headers,
            'time': grab.response_time(),
            'code': grab.response_code,
            'curl': grab.curl,
            'status': grab.response_status,
            'get_soup': lambda: grab.soup,
    }


def main():
    # testing
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
    g = Grab()
    g.setup(log_dir='var')
    g.setup(url='ya.ru')
    #~ g.setup(url='http://webmaster.yandex.ru/check.xml')
    #~ print g.config
    g.request()


def REX_INPUT(name):
    return re.compile(r'<input[^>]+name\s*=\s*["\']?%s["\' ][^>]*>' % re.escape(name), re.S)
REX_VALUE = re.compile(r'value\s*=\s*["\']?([^"\'> ]+)', re.S)

def clone_config(cfg):
    """
    Works faster than deepcopy.
    """

    res = {}
    for key, value in cfg.iteritems():
        if isinstance(value, (list, dict)):
            res[key] = copy(value)
        else:
            res[key] = copy(value)
    return res


def default_config(): return dict(
    timeout = 15,
    connect_timeout = 10,
    proxy = None,
    proxy_type = None,
    proxy_userpwd = None,
    proxy_file = None,
    proxy_random = True,
    proxy_list = False,
    post = None,
    payload = None,
    method = None,
    headers = {
        'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.%d' % randint(2, 5),
        'Accept-Language': 'en-us;q=0.%d,en,ru;q=0.%d' % (randint(5, 9), randint(1, 4)),
        'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.%d' % randint(5, 7),
        'Keep-Alive': '300',
    },
    charset = 'utf-8',
    user_agent = choice(user_agent.variants),
    reuse_cookies = True,
    reuse_referer = True,
    cookies = {},
    referer = None,
    unicode_body = False,
    guess_encodings = ['windows-1251', 'koi8-r', 'utf-8'],
    log_file = None,
    log_dir = False,
    follow_refresh = False,
    nohead = False,
    nobody = False,
    remove_scripts = True,
    debug = False,
)


class Grab(object):
    Error = GrabError
    counter = -1

    def __init__(self):
        self.config = default_config()
        self.curl = pycurl.Curl()
        self.reset()

    def clone(self):
        g = Grab()
        g.config = clone_config(self.config)
        g.setup(cookies=self.cookies)

        keys = ['response_status', 'response_code', 'response_head',
                'response_body',
                'headers', 'cookies', 'counter', '_soup']
        for key in keys:
            setattr(g, key, getattr(self, key))

        return g

    def setup(self, **kwargs):
        if 'headers' in kwargs:
            self.config['headers'].update(kwargs['headers'])
        self.config.update(kwargs)

    def head_processor(self, data):
        if self.config['nohead']:
            return 0
        self.response_head.append(data)
        return len(data)

    def body_processor(self, data):
        if self.config['nobody']:
            return 0
        self.response_body.append(data)
        return len(data)

    def debug_processor(self, _type, text):
        if _type == pycurl.INFOTYPE_HEADER_OUT:
            text = '\n'.join(text.splitlines()[1:])
            self.request_headers = dict(email.message_from_string(text))

    def process_config(self):
        """
        Setup curl instance with the config.
        """

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
        self.curl.setopt(pycurl.USERAGENT, self.config['user_agent'])

        if self.config['debug']:
            self.curl.setopt(pycurl.VERBOSE, 1)
            self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        # Ignore SSL errors
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        method = (self.config['method'] or '').upper()

        if not method:
            if self.config['payload'] or self.config['post']:
                method = 'POST'
            else:
                method = 'GET'

        if method == 'POST':
            self.curl.setopt(pycurl.POST, 1)
            if self.config['payload']:
                self.curl.setopt(pycurl.POSTFIELDS, self.config['payload'])
            elif self.config['post']:
                post_data = self.urlencode(self.config['post'])
                self.curl.setopt(pycurl.POSTFIELDS, post_data)
        elif method == 'PUT':
            self.curl.setopt(pycurl.PUT, 1)
            self.curl.setopt(pycurl.READFUNCTION, StringIO(self.config['payload']).read) 
        elif method == 'DELETE':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        else:
            # Assume the GET method
            self.curl.setopt(pycurl.HTTPGET, 1)
        
        log.debug('[%02d] %s %s' % (self.counter, method, self.config['url']))

        if self.config['headers']:
            headers = [str('%s: %s' % x) for x\
                       in self.config['headers'].iteritems()]
            self.curl.setopt(pycurl.HTTPHEADER, headers)


        # CURLOPT_COOKIELIST
        # Pass a char * to a cookie string. Cookie can be either in Netscape / Mozilla format or just regular HTTP-style header (Set-Cookie: ...) format. If cURL cookie engine was not enabled it will enable its cookie engine. Passing a magic string "ALL" will erase all cookies known by cURL. (Added in 7.14.1) Passing the special string "SESS" will only erase all session cookies known by cURL. (Added in 7.15.4) Passing the special string "FLUSH" will write all cookies known by cURL to the file specified by CURLOPT_COOKIEJAR. (Added in 7.17.1)

        if self.config['reuse_cookies']:
            self.curl.setopt(pycurl.COOKIELIST, '')
        else:
            self.curl.setopt(pycurl.COOKIELIST, 'ALL')


        #CURLOPT_COOKIE
        # Pass a pointer to a zero terminated string as parameter. It will be used to set a cookie in the http request. The format of the string should be NAME=CONTENTS, where NAME is the cookie name and CONTENTS is what the cookie should contain.
        # If you need to set multiple cookies, you need to set them all using a single option and thus you need to concatenate them all in one single string. Set multiple cookies in one string like this: "name1=content1; name2=content2;" etc.
        # Note that this option sets the cookie header explictly in the outgoing request(s). If multiple requests are done due to authentication, followed redirections or similar, they will all get this cookie passed on.
        # Using this option multiple times will only make the latest string override the previous ones. 

        if self.config['cookies']:
            chunks = []
            for key, value in self.config['cookies'].iteritems():
                key = urllib.quote_plus(key)
                value = urllib.quote_plus(value)
                chunks.append('%s=%s;' % (key, value))
            self.curl.setopt(pycurl.COOKIE, ''.join(chunks))

        if self.config['referer']:
            self.curl.setopt(pycurl.REFERER, str(self.config['referer']))


        if self.config['proxy']:
            # str is required to force unicode values
            self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 

            # Pass a long with this option to set type of the proxy. Available options for this are CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4), CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5, CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0). The HTTP type is default. (Added in 7.10) 
            if self.config['proxy_userpwd']:
                self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])


        if self.config['proxy_type']:
            ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
            self.curl.setopt(pycurl.PROXYTYPE, ptype)

        if self.config['proxy']:
            if self.config['proxy_userpwd']:
                auth = ' with authorization'
            else:
                auth = ''
            log.debug('Using proxy %s of type %s%s' % (
                self.config['proxy'], self.config['proxy_type'], auth))


    def parse_headers(self):
        #for line in re.split('\r?\n', self.response_head):
        for line in self.response_head.split('\n'):
            line = line.rstrip('\r')
            if line.startswith('HTTP'):
                self.response_status = line
            try:
                name, value = line.split(': ', 1)
                self.headers[name] = value
            except ValueError:
                pass

    def parse_cookies(self):
        for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            # Example of line:
            # www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
            chunks = line.split('\t')
            self.cookies[chunks[-2]] = chunks[-1]

    def reset(self):
        self.response_status = None
        self.response_code = None
        self.response_head = []
        self.response_body = []
        self.request_headers = None
        self.headers = {}
        self.cookies = {}
        self.counter += 1
        self._soup = None
        self._tree = None
        self._form = None

    def go(self, url):
        if self.config.get('url'):
            url = urljoin(self.config['url'], url)
        return self.request(url=url)

    def request(self, **kwargs):
        if kwargs:
            self.setup(**kwargs)
        self.reset()
        self.process_config()
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
                raise GrabError(ex[0], ex[1])

        if self.config['post']:
            print 'POST: %s' % self.config['post']
        print 'REQUEST: %s' % self.request_headers

        # It is very importent to delete old POST data after
        # request. In other case such data will be used again
        # in next request :-/
        self.config['post'] = None
        self.config['payload'] = None
        self.config['method'] = None

        self.response_code = self.curl.getinfo(pycurl.HTTP_CODE)
        #if 400 <= self.response_code:
            #raise IOError('Response code is %s: ' % self.response_code)
        self.response_head = ''.join(self.response_head)
        self.response_body = ''.join(self.response_body)

        self.parse_cookies()
        self.parse_headers()

        if self.config['log_file']:
            open(self.config['log_file'], 'w').write(self.response_body)

        if self.config['log_dir']:
            tname = threading.currentThread().getName().lower()
            if tname == 'mainthread':
                tname = ''
            else:
                tname = '-%s' % tname
            fname = os.path.join(self.config['log_dir'], '%02d%s.log' % (self.counter, tname))
            open(fname, 'w').write(self.response_head)

            fext = 'html'
            #dirs = self.response_url().split('//')[1].strip().split('/')
            #if len(dirs) > 1:
                #fext = dirs[-1].split('.')[-1]
                
            fname = os.path.join(self.config['log_dir'], '%02d%s.%s' % (self.counter, tname, fext))
            open(fname, 'w').write(self.response_body)

        if self.config['reuse_referer']:
            self.config['referer'] = self.response_url()

        if self.config['follow_refresh']:
            url = find_refresh_url(self.response_body)
            if url:
                # TODO check max redirect count
                self.setup(url=url)
                return self.request()

    def response_time(self):
        return self.curl.getinfo(pycurl.TOTAL_TIME)

    def response_url(self):
        return self.curl.getinfo(pycurl.EFFECTIVE_URL)

    @property
    def soup(self):
        if not self._soup:
            from BeautifulSoup import BeautifulSoup
            # Do some magick to make BeautifulSoup happy
            if self.config['remove_scripts']:
                data = SCRIPT_TAG.sub(r'\1\2', self.response_body)
            else:
                data = self.response_body
            self._soup = BeautifulSoup(data)
        return self._soup


    @property
    def legacy_etree(self):
        """
        Return the root of tree builded with ElementTree API of lxml library.
        Note that this API is extended version of standart ElementTree API of
        xml.etree module. For example lxml library provide xpath method for the
        ``Element`` instances.
        """

        import html5lib
        # First use the html5lib. If it fails try to use lxml parser.
        try:
            return html5lib.parse(self.response_body, treebuilder='lxml', namespaceHTMLElements=False).getroot()
        except Exception:
            return self.tree
            #return etree.parse(StringIO(self.response_body), etree.HTMLParser()).getroot()


    @property
    def tree(self):
        if self._tree is None:
            from lxml.html import fromstring
            self._tree = fromstring(self.response_body)
        return self._tree


    def input_value(self, name):
        """
        Return the value of INPUT element.
        """

        try:
            elem = REX_INPUT(name).search(self.response_body).group(0)
        except AttributeError:
            return None
        else:
            try:
                return REX_VALUE.search(elem).group(1)
            except AttributeError:
                return None

    def repeat(self, anchor, action=None, number=10, args=None):
        """
        Make requests until "anchor" string will be found in response
        or number of requests exeeds the "number".
        """

        for x in xrange(number):
            if args:
                self.setup(**args)
            if action:
                action()
            else:
                self.request()
            
            if isinstance(anchor, (list, tuple)):
                searches = anchor
            else:
                searches = [anchor]
            for search in searches:
                if search in self.response_body:
                    return
        else:
            message = 'Substring "%s" not found in response.' % anchor
            if isinstance(message, unicode):
                message = message.encode('utf-8')
            raise IOError(message)

    def get_form(number=0):
        return self.soup.findAll('form')[number]

    @property
    def unicode_response_body(self):
        return make_unicode(self.response_body, self.config['guess_encodings'])

    def follow_link(self, anchor=None, href=None):
        if anchor is None and href is None:
            raise Exception('You have to provide anchor or href argument')
        self.tree.make_links_absolute(self.config['url'])
        #import pdb; pdb.set_trace()
        for item in self.tree.iterlinks():
            if item[0].tag == 'a':
                found = False
                text = item[0].text or u''
                url = item[2]
                # if object is regular expression
                if anchor:
                    if hasattr(anchor, 'finditer'):
                        if anchor.search(text):
                            found = True
                    else:
                        if text.find(anchor) > -1:
                            found = True
                if href:
                    if hasattr(href, 'finditer'):
                        if href.search(url):
                            found = True
                    else:
                        if url.startswith(href) > -1:
                            found = True
                if found:
                    url = urljoin(self.config['url'], item[2])
                    return self.request(url=item[2])
        raise DataNotFound('Cannot find link ANCHOR=%s, HREF=%s' %\
                           (anchor, href))

    def choose_form(self, index):
        self._form = self.tree.forms[index]

    @property
    def form(self):
        if self._form is None:
            # Automatically select the form with most big number of fields
            forms = [(idx, len(x.fields)) for idx, x in enumerate(self.tree.forms)]
            idx = sorted(forms, key=lambda x: x[1], reverse=True)[0][0]
            self.choose_form(idx)
        return self._form

    def set_input(self, name, value):
        elem = self.form.inputs[name]

        processed = False
        if getattr(elem, 'type', None) == 'checkbox':
            if isinstance(value, bool):
                elem.checked = value
                processed = True
        
        if not processed:
            elem.value = value

    def set_input_by_id(self, _id, value):
        name = self.tree.xpath('//*[@id="%s"]' % _id)[0].get('name')
        return self.set_input(name, value)

    def set_inputs(self, arg):
        if not isinstance(arg, dict):
            arg = dict(arg)
        for key, value in arg.iteritems():
            self.set_input(key, value)

    def set_inputs_by_id(self, arg):
        if not isinstance(arg, dict):
            arg = dict(arg)
        for _id, value in arg.iteritems():
            self.set_input_by_id(_id, value)

    def submit(self, button_name=None):
        action_url = urljoin(self.config['url'], self.form.action)
        self.setup(url=action_url)
        post = dict(self.form.fields)
        for elem in self.form.inputs:
            if elem.tag == 'select':
                if not post[elem.name]:
                    post[elem.name] = elem.value_options[-1]
        #import pdb; pdb.set_trace()
        # TODO: check out how to handle forms
        # with multiple submit buttons
        #if not button_name in post:
            #if button_name is not None:
                #post[button_name] = '
        if self.form.method == 'POST':
            self.setup(post=post)
        else:
            url = action_url.split('?')[0] + '?' + self.urlencode(post.items())
            self.setup(url=url)
        return self.request()

    def urlencode(self, items):
        if isinstance(items, dict):
            items = items.items()
        def process(item):
            key, value = item
            if isinstance(value, unicode):
                value = value.encode(self.config['charset'])
            elif value is None:
                value = ''
            return key, value
        items = urllib.urlencode(map(process, items))
        logging.debug(items)
        return items

    def search(self, anchor):
        if hasattr(anchor, 'finditer'):
            return anchor.search(self.response_body) or None
        if isinstance(anchor, unicode):
            anchor = anchor.encode(self.config['charset'])
        return anchor if self.response_body.find(anchor) > -1 else None

    def search_rex(self, rex, flags=0):
        if not hasattr(rex, 'finditer'):
            rex = re.compile(rex, flags)
        return rex.search(self.response_body) or None

    def assert_string(self, *args, **kwargs):
        if not self.search(*args, **kwargs):
            raise DataNotFound(u'Could not found string: %s' % anchor)

    def assert_rex(self, *args, **kwargs):
        if not self.search_rex(*args, **kwargs):
            raise DataNotFound(u'Could not found regexp')

    def xpath(self, path):
        return self.tree.xpath(path)

    def reload(self):
        g.go('')

    @property
    def response(self):
        class Foo(object):
            body = self.response_body
        return Foo()


if __name__ == "__main__":
    main()
