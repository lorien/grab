.. _grab_cookies:

Cookie Support
==============

By default, Grab automatically handles all cookies it receives from the remote server. Grab remembers all cookies and
sends them back in future requests. That allows you to easily implement scripts that log in to some site and then do
some activity in a member-only area. If you do not want Grab to automatically process cookies,
use :ref:`option_reuse_cookies` option to disable it.

Custom Cookies
--------------

To send some custom cookies, use the :ref:`option_cookies` option. The value of that option should be a dict.
When you specify some cookies with :ref:`option_cookies` option and then fire network request, all specified
cookies are bound to the hostname of the request.

Internally Grab instance stores cookies in `http.cookiejar:CookieJar` instance.

It is important to understand that Response object contains only cookies has been provided by the server in
recent HTTP response. If you need all session cookies use "Grab:cookies" attribute.

If you want more granular control on custom cookies, you can
use the `grab.util.cookies.create_cookie` function to create Cookie object and add its to Grab instance::

    >>> from grab.util.cookies import create_cookie
    >>> g = Grab()
    >>> g.cookies.set_cookie(create_cookie(name='foo', value='bar', domain='yandex.ru', path='/host'))
