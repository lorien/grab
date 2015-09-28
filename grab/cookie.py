"""
RTFM:

* http://docs.python.org/2/library/cookielib.html#cookie-objects

Some code got from
    https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
"""
from __future__ import absolute_import
from six.moves.http_cookiejar import CookieJar, Cookie
import json
import logging

from grab.error import GrabMisuseError
from six.moves.urllib.parse import urlparse

logger = logging.getLogger('grab.cookie')
COOKIE_ATTRS = ('name', 'value', 'version', 'port', 'domain',
                'path', 'secure', 'expires', 'discard', 'comment',
                'comment_url', 'rfc2109')


# Source: https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
class MockRequest(object):
    """Wraps a `requests.Request` to mimic a `urllib2.Request`.
    The code in `cookielib.CookieJar` expects this interface in order to correctly
    manage cookie policies, i.e., determine whether a cookie can be set, given the
    domains of the request and the cookie.
    The original request object is read-only. The client is responsible for collecting
    the new headers via `get_new_headers()` and interpreting them appropriately. You
    probably want `get_cookie_header`, defined below.
    """

    def __init__(self, request):
        self._r = request
        self._new_headers = {}
        self.type = urlparse(self._r.url).scheme

    def get_type(self):
        return self.type

    def get_host(self):
        return urlparse(self._r.url).netloc

    def get_origin_req_host(self):
        return self.get_host()

    def get_full_url(self):
        # Only return the response's URL if the user hadn't set the Host
        # header
        if not self._r.headers.get('Host'):
            return self._r.url
        # If they did set it, retrieve it and reconstruct the expected domain
        host = self._r.headers['Host']
        parsed = urlparse(self._r.url)
        # Reconstruct the URL as we expect it
        return urlunparse([
            parsed.scheme, host, parsed.path, parsed.params, parsed.query,
            parsed.fragment
        ])

    def is_unverifiable(self):
        return True

    def has_header(self, name):
        return name in self._r.headers or name in self._new_headers

    def get_header(self, name, default=None):
        return self._r.headers.get(name, self._new_headers.get(name, default))

    def add_header(self, key, val):
        """cookielib has no legitimate use for this method; add it back if you find one."""
        raise NotImplementedError("Cookie headers should be added with add_unredirected_header()")

    def add_unredirected_header(self, name, value):
        self._new_headers[name] = value

    def get_new_headers(self):
        return self._new_headers

    @property
    def unverifiable(self):
        return self.is_unverifiable()

    @property
    def origin_req_host(self):
        return self.get_origin_req_host()

    @property
    def host(self):
        return self.get_host()


# https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
class MockResponse(object):
    """Wraps a `httplib.HTTPMessage` to mimic a `urllib.addinfourl`.
    ...what? Basically, expose the parsed HTTP headers from the server response
    the way `cookielib` expects to see them.
    """

    def __init__(self, headers):
        """Make a MockResponse for `cookielib` to read.
        :param headers: a httplib.HTTPMessage or analogous carrying the headers
        """
        self._headers = headers

    def info(self):
        return self._headers

    def getheaders(self, name):
        self._headers.getheaders(name)


def create_cookie(name, value, domain, httponly=None, **kwargs):
    "Creates `cookielib.Cookie` instance"

    if domain == 'localhost':
        domain = ''
    config = dict(
        name=name,
        value=value,
        version=0,
        port=None,
        domain=domain,
        path='/',
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rfc2109=False,
        rest={'HttpOnly': httponly},
    )

    for key in kwargs.keys():
        if key not in config:
            raise GrabMisuseError('Function `create_cookie` does not accept '
                                  '`%s` argument' % key)

    config.update(**kwargs)
    config['rest']['HttpOnly'] = httponly

    config['port_specified'] = bool(config['port'])
    config['domain_specified'] = bool(config['domain'])
    config['domain_initial_dot'] = (config['domain'] or '').startswith('.')
    config['path_specified'] = bool(config['path'])

    return Cookie(**config)


class CookieManager(object):
    """
    Each Grab instance has `cookies` attribute that is instance of
    `CookieManager` class.

    That class contains helpful methods to create, load, save cookies from/to
    different places.
    """

    __slots__ = ('cookiejar',)

    def __init__(self, cookiejar=None):
        if cookiejar is not None:
            self.cookiejar = cookiejar
        else:
            self.cookiejar = CookieJar()
        # self.disable_cookiejar_lock(self.cookiejar)

    # def disable_cookiejar_lock(self, cj):
        # cj._cookies_lock = dummy_threading.RLock()

    def set(self, name, value, domain, **kwargs):
        """Add new cookie or replace existing cookie with same parameters.

        :param name: name of cookie
        :param value: value of cookie
        :param kwargs: extra attributes of cookie
        """

        if domain == 'localhost':
            domain = ''

        self.cookiejar.set_cookie(create_cookie(name, value, domain, **kwargs))

    def update(self, cookies):
        if isinstance(cookies, CookieJar):
            for cookie in cookies:
                self.cookiejar.set_cookie(cookie)
        elif isinstance(cookies, CookieManager):
            for cookie in cookies.cookiejar:
                self.cookiejar.set_cookie(cookie)
        else:
            raise GrabMisuseError('Unknown type of cookies argument: %s'
                                  % type(cookies))

    @classmethod
    def from_cookie_list(cls, clist):
        cj = CookieJar()
        for cookie in clist:
            cj.set_cookie(cookie)
        return cls(cj)

    def clear(self):
        self.cookiejar = CookieJar()

    def __getstate__(self):
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, '__slots__', ())
            for slot in cls_slots:
                if slot != '__weakref__':
                    if hasattr(self, slot):
                        state[slot] = getattr(self, slot)

        state['_cookiejar_cookies'] = list(self.cookiejar)
        del state['cookiejar']

        return state

    def __setstate__(self, state):
        state['cookiejar'] = CookieJar()
        for cookie in state['_cookiejar_cookies']:
            state['cookiejar'].set_cookie(cookie)
        del state['_cookiejar_cookies']

        for slot, value in state.items():
            setattr(self, slot, value)

    def __getitem__(self, key):
        for cookie in self.cookiejar:
            if cookie.name == key:
                return cookie.value
        raise KeyError

    def items(self):
        res = []
        for cookie in self.cookiejar:
            res.append((cookie.name, cookie.value))
        return res

    def load_from_file(self, path):
        """
        Load cookies from the file.

        Content of file should be a JSON-serialized list of dicts.
        """

        with open(path) as inf:
            data = inf.read()
            if data:
                items = json.loads(data)
            else:
                items = {}
        for item in items:
            extra = dict((x, y) for x, y in item.items()
                         if x not in ['name', 'value', 'domain'])
            self.set(item['name'], item['value'], item['domain'], **extra)

    def get_dict(self):
        res = []
        for cookie in self.cookiejar:
            res.append(dict((x, getattr(cookie, x)) for x in COOKIE_ATTRS))
        return res

    def save_to_file(self, path):
        """
        Dump all cookies to file.

        Cookies are dumped as JSON-serialized dict of keys and values.
        """

        with open(path, 'w') as out:
            out.write(json.dumps(self.get_dict()))

    def get_cookie_header(self, req):
        """
        :param req: object with httplib.Request interface
            Actually, it have to have `url` and `headers` attributes
        """
        mocked_req = MockRequest(req)
        self.cookiejar.add_cookie_header(mocked_req)
        return mocked_req.get_new_headers().get('Cookie') 
