"""
RTFM:

* http://docs.python.org/2/library/cookielib.html#cookie-objects

Some code got from https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
"""
import cookielib


def create_cookie(name, value, **kwargs):
    
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


    return cookielib.Cookie(**config)
