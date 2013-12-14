.. _grab_proxy:

Proxy Server Support
====================

Basic Usage
-----------

To make Grab send requests via proxy server use :ref:`option_proxy` option::

    g.setup(proxy='example.com:8080')

If the proxy server requires authentication use :ref:`option_proxy_usrpwd` option
to specify the username and the password::

    g.setup(proxy='example.com:8080', proxy_userpwd='root:777')

Also you can specify the type of proxy server: "http", "socks4" or "socks5". By default,
Grab assumes that proxy is of "http" type::

    g.setup(proxy='example.com:8080', proxy_userpwd='root:777', proxy_type='socks5')

You can always see what proxy is used at the moment in `g.config['proxy']`::

    >>> g = Grab()
    >>> g.setup(proxy='example.com:8080')
    >>> g.config['proxy']
    'example.com:8080'

Proxy List Support
------------------

Grab supports work with multiple proxy list. Use `g.proxylist`
attribute to get access to proxy manager. By default, proxy manager is created and initialized with empty proxy list::

    >>> g = Grab()
    >>> g.proxylist
    <grab.proxy.ProxyList object at 0x2e15b10>
    >>> g.proxylist.proxy_list
    []


Proxy List Source
-----------------

You need to setup proxy list manager with details of source that
manager will load proxies from. Use `g.proxylist.set_source` method those first
positional argument defines the type of source. Currently, two types are supported: 
"file" and "remote"

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


And that is how to load proxies from the web::

    >>> g = Grab()
    >>> g.proxylist.set_source('remote', url='http://example.com/proxy.txt')


Proxy Rotation
--------------

Each time you call `g.proxylist.get_next_proxy` method you get next proxy from the proxy list. After you received last proxy you'll continue receiving proxies from the start of the list. Also, you can use `g.proxylist.get_random_proxy` to pick up random proxy from the proxy list.


Automatic Proxy List Reloading
------------------------------

Grab automatically reread the proxy source each `g.proxylist.reload_time` seconds. You can control this value in this way::

    >>> g = Grab()
    >>> g.proxylist.setup(reload_time=3600) # reload proxy list one time per hour
    

Proxy Accumulating
------------------

Be default, Grab overwrite proxy list each time it reloads the proxy source. You can change that behaviuour::

    >>> g.proxylist.setup(accumulate_updates=True)

That will setup Grab to append new proxies to existing ones.
