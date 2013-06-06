.. _spider_cache:

=======================
The network cache layer
=======================

The network cache layer was developed by two reasons:

* to speed up the process of testing and debugging the spider
* to speed up the scraping of pages that already were processed some time ago

The cache has limitation. It can store only pages which was downloaded with GET request.
The network cache layer is not full-featured proxy service, it is very simple. But even being
such simple the network layer helps very much.

Cache backend
=============

The cache layer allows to use different storages for storing the cached pages. Now three backends are available: mongodb, mysql and tokyo cabinet.

How to enable the cache
=======================

To allow the spider to search requested documents in the cache and to save received data into cache you need to call `setup_cache` method before spider started working::

    bot = ExampleSpider()
    bot.setup_cache(...)
    bot.run()

The `setup_cache` method requires two arguments:

    :param backend: type of storage: "mongo", "mysql" or "tokyo_cabinet"
    :param database: name of mongo collection, mysql database or tokyo cabinet file

Any other arguments you pass to the `setup_cache` method will goes to the backend's specific
function which creates connection to the backend. For better understanding how it works see
the source code of the specific cache backend.

Mongodb cache
=============

To enable mongodb cache use::

    bot.setup_cache(backend='mongo', database='imdb')

This code instruct spider to use `cache` collection in mongo database called `imdb`.

MySQL cache
===========

To enable mongodb cache use::

    bot.setup_cache(backend='mysql', database='imdb')

This code instruct spider to use `cache` table in mysql database called `imdb`.

You can additional arguments, any arguments which are valid for `MySQLdb.connect` method. Here
is example of passing username and password::

    bot.setup_cache(backend='mysql', database='imdb',
                    user='root', passwd='123')

Tokyo Cabinet Cache
===================

To enable tokyo cabinet cache use::

    bot.setup_cache(backend='tokyo_cabinet', database='/path/to/file')

This code instruct spider to use file located at /path/to/file as tokyo cabinet database.

Cache compression
=================

All documents which are stored into the cache are compressed with zlib library.

Control the cache usage
=======================

When you create new network task you can control how it will be handled by cache layer. By-default
the network requests is not performed if corresponding record was found in the cache. Also by-default result of any network request is saved into cache.

If you need to force the real network request and update the cache::

    >>> Task('some-name, url='some_url', refresh_cache=True)

If you need to force the real network request and not update the cached version::

    >>> Task('some-name, url='some_url', disable_cache=True)

You can pass `cache_timeout` argument which control how many seconds the recourd could be
old to be valid::

    >>> Task('some-name', url='some_url', cache_timeout=60 * 60 * 24)

Clear the cache
===============

You can clear all cache contents with `clear` method::

    >>> bot.setup_cache(...)
    >>> bot.cache.clear()
