.. _grab_cookies:

Cookies Support
===============

By default, Grab automatically handles all cookies it receives from the remote server. Grab remember all cookies and sends them back in farther requests. That allows you to easily implement scripts that logs in to some site and then do some activity in member-only area. If you do not want Grab to automatically process cookies, use :ref:`option_reuse_cookies` option to disable it.

Custom Cookies
--------------

To send some custom cookies use :ref:`option_cookies` option. The value of that option should be a dict. When you specify some cookies with :ref:`option_cookies` option and then do request, all specified cookies are bound to the hostname of the request. If you wnat more granular control on custom cookies, you can use `grab.cookies` object to specify a cookie with any attributes you want::

    >>> g = Grab()
    >>> g.cookies.set(name='foo', value='bar', domain='yandex.ru', path='/host')

More details about `grab.cookies` you can get in :ref:`api_grab_cookie` 
