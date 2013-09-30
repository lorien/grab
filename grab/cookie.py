"""
RTFM:

* http://docs.python.org/2/library/cookielib.html#cookie-objects

Some code got from https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
"""
from cookielib import Cookie, CookieJar

from .error import GrabMisuseError

def create_cookie(name, value, **kwargs):
    """Creates `cookielib.Cookie` instance.
    """

    config = dict(
        name=name,
        value=value,
        version=0,
        port=None,
        domain='',
        path='/',
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rfc2109=False,
        rest={'HttpOnly': None},  # wtf?
    )

    bad_args = set(kwargs) - set(config.keys())
    if bad_args:
        raise TypeError('Unexpected arguments: %s' % tuple(bad_args))

    config.update(**kwargs)

    config['port_specified'] = bool(config['port'])
    config['domain_specified'] = bool(config['domain'])
    config['domain_initial_dot'] = config['domain'].startswith('.')
    config['path_specified'] = bool(config['path'])

    return Cookie(**config)


class CookieManager(object):
    """
    The instance of that class operates with cookies of one Grab instance.

    That class contains helpful methods to create, load, save cookies from/to
    different places.
    """

    __slots__ = ('cookiejar',)

    def __init__(self, cookiejar=None):
        if cookiejar is not None:
            self.cookiejar = cookiejar
        else:
            self.cookiejar = CookieJar()

    def update(self, cookies):
        if isinstance(cookies, CookieJar):
            for cookie in cookies:
                self.cookiejar.set_cookie(cookie)
        elif isinstance(cookies, CookieManager):
            for cookie in cookies.cookiejar:
                self.cookiejar.set_cookie(cookie)
        else:
            raise GrabMisuseError('Unknown type of cookies argument: %s' % type(cookies))

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
