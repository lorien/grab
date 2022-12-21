.. _grab_proxy:

Proxy Server Support
====================

Basic Usage
-----------

To make Grab send requests through a proxy server, use the :ref:`option_proxy` option::

    g.setup(proxy='example.com:8080')

If the proxy server requires authentication, use the :ref:`option_proxy_userpwd` option
to specify the username and password::

    g.setup(proxy='example.com:8080', proxy_userpwd='root:777')

You can also specify the type of proxy server: "http", "socks4" or "socks5". By default,
Grab assumes that proxy is of type "http"::

    g.setup(proxy='example.com:8080', proxy_userpwd='root:777', proxy_type='socks5')

You can always see which proxy is used at the moment in `g.config['proxy']`::

    >>> g = Grab()
    >>> g.setup(proxy='example.com:8080')
    >>> g.config['proxy']
    'example.com:8080'

Proxy List Support
------------------

Grab supports a work with a list of proxy servers. You need to manually create instance of ProxyList class from "proxylist" package (it
is installed along Grab) and assign it to `g.proxylist` attribute. When you create ProxyList instance do not forget to specify the default
proxy type ("socks5" or "http"), if proxy list does not provide information about proxy the Grab raises runtime error.

Loading proxy list from local file:

    >>> from proxylist import Proxylist
    >>> g = Grab()
    >>> g.proxylist = ProxyList.from_local_file("var/proxy.txt", proxy_type="socks5")

Loading proxy list from network:

    >>> from proxylist import Proxylist
    >>> g = Grab()
    >>> g.proxylist = ProxyList.from_network_file("https://example.com/proxy.txt", proxy_type="socks5")

For more information about ProxyList class please refer to https://proxylist.readthedocs.io


Automatic Proxy Rotation
------------------------

By default, if you set up any non-empty proxy source, Grab starts rotating through proxies from the proxy list for each request.
You can disable proxy rotation with :ref:`option_proxy_auto_change` option set to False::

    >>> from grab import Grab
    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)
    >>> g = Grab()
    >>> g.proxylist = ProxyList.from_local_file("/web/proxy.txt", proxy_type="http")
    >>> g.request('http://yandex.ru/')
    DEBUG:grab.network:[02] GET http://yandex.ru/ via 91.210.101.31:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>
    >>> g.request('http://rambler.ru/')
    DEBUG:grab.network:[03] GET http://rambler.ru/ via 194.29.185.38:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>

Now let's see how Grab works when `proxy_auto_change` is False::

    >>> from grab import Grab
    >>> import logging
    >>> g = Grab()
    >>> g.proxylist = ProxyList.from_local_file("/web/proxy.txt", proxy_type="http")
    >>> g.setup(proxy_auto_change=False)
    >>> g.request('http://ya.ru')
    DEBUG:grab.network:[04] GET http://ya.ru
    <grab.response.Response object at 0x109de50>
    >>> g.change_proxy()
    >>> g.request('http://ya.ru')
    DEBUG:grab.network:[05] GET http://ya.ru via 62.122.73.30:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>
    >>> g.request('http://ya.ru')
    DEBUG:grab.network:[06] GET http://ya.ru via 62.122.73.30:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>


Getting Proxy From Proxy List
-----------------------------

Each time you call `g.proxylist.get_next_server()`, you get the next proxy from the proxy list.
When you receive the last proxy in the list, you'll continue receiving proxies from the beginning of the list.
You can also use `g.proxylist.get_random_server()` to pick a random proxy from the proxy list.
