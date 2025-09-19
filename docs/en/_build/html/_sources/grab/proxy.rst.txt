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

Grab supports working with a list of multiple proxies. Use the `g.proxylist`
attribute to get access to the proxy manager. By default, the proxy manager is created and initialized with an empty proxy list::

    >>> g = Grab()
    >>> g.proxylist
    <grab.proxy.ProxyList object at 0x2e15b10>
    >>> g.proxylist.proxy_list
    []


Proxy List Source
-----------------

You need to setup the proxy list manager with details of the source that
manager will load proxies from. Using the `g.proxylist.set_source` method, the first
positional argument defines the type of source. Currently, two types are supported: 
"file" and "remote".

Example of loading proxies from local file::

    >>> g = Grab()
    >>> g.proxylist.set_source('file', location='/web/proxy.txt')
    <grab.proxy.ProxyList object at 0x2e15b10>
    >>> g.proxylist.proxy_list
    >>> g.proxylist.set_source('file', location='/web/proxy.txt')
    >>> g.proxylist.get_next()
    >>> g.proxylist.get_next_proxy()
    <grab.proxy.Proxy object at 0x2d7c610>
    >>> g.proxylist.get_next_proxy().server
    'example.com'
    >>> g.proxylist.get_next_proxy().address
    'example.com:8080'
    >>> len(g.proxylist.proxy_list)
    1000


And here is how to load proxies from the web::

    >>> g = Grab()
    >>> g.proxylist.set_source('remote', url='http://example.com/proxy.txt')


Automatic Proxy Rotation
------------------------

By default, if you set up any non-empty proxy source, Grab starts rotating through proxies from the proxy list for each request.
You can disable proxy rotation with :ref:`option_proxy_auto_change` option set to False::

    >>> from grab import Grab
    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)
    >>> g = Grab()
    >>> g.proxylist.set_source('file', location='/web/proxy.txt')
    >>> g.go('http://yandex.ru/')
    DEBUG:grab.network:[02] GET http://yandex.ru/ via 91.210.101.31:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>
    >>> g.go('http://rambler.ru/')
    DEBUG:grab.network:[03] GET http://rambler.ru/ via 194.29.185.38:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>

Now let's see how Grab works when `proxy_auto_change` is False::

    >>> from grab import Grab
    >>> import logging
    >>> g = Grab()
    >>> g.proxylist.set_source('file', location='/web/proxy.txt')
    >>> g.setup(proxy_auto_change=False)
    >>> g.go('http://ya.ru')
    DEBUG:grab.network:[04] GET http://ya.ru
    <grab.response.Response object at 0x109de50>
    >>> g.change_proxy()
    >>> g.go('http://ya.ru')
    DEBUG:grab.network:[05] GET http://ya.ru via 62.122.73.30:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>
    >>> g.go('http://ya.ru')
    DEBUG:grab.network:[06] GET http://ya.ru via 62.122.73.30:8080 proxy of type http with authorization
    <grab.response.Response object at 0x109d9f0>


Getting Proxy From Proxy List
-----------------------------

Each time you call `g.proxylist.get_next_proxy`, you get the next proxy from the proxy list.
When you receive the last proxy in the list, you'll continue receiving proxies from the beginning of the list.
You can also use `g.proxylist.get_random_proxy` to pick a random proxy from the proxy list.

Automatic Proxy List Reloading
------------------------------

Grab automatically rereads the proxy source each `g.proxylist.reload_time`
seconds. You can set the value of this option as follows::

    >>> g = Grab()
    >>> g.proxylist.setup(reload_time=3600) # reload proxy list one time per hour
    

Proxy Accumulating
------------------

Be default, Grab overwrites the proxy list each time it reloads the proxy source. You can change that behaviour::

    >>> g.proxylist.setup(accumulate_updates=True)

That will setup Grab to append new proxies to existing ones.
