.. _spider_cache:

Spider Cache
============

There is cache built in the spider. It could be helpful on development stage.
When you need to scrape same documents for many times to check the results
and to fix bugs. Also you can crawl whole web-site, put it into cache and
then work only with cache.

Keep in mind that if the web-site is large, millions of web pages then working
with cache could be slower than working with live web-site. This is because of
limited disk I/O where the cache storage is hosted.

Also keep in mind the the spider cache is very simple:

* it allows to cache only GET requests
* it does not allow to diffirentiate documents with same URL but
    different cookies/headers
* it does not support max-age and other cache headers


.. _spider_cache_backends:

Spider Cache Backends
---------------------

You can choose what storage to use for the cache. You can use mongodb, mysql
and postgresql.

MongoDB example:

.. code:: python

    bot = ExampleSpider()
    bot.setup_cache(backend='mongo', database='some-database')
    bot.run()

In this example the spider is configured to use mongodb as cache storage.
The name of database is "some-database". The name of collection would
be "cache".

All arguments except `backend`, `database` and `use_compression` go to
database connection constructor. You can setup database name, host name, port,
authorization arguments and other things.

Example of custom host name and port for mongodb connection::

.. code:: python

    bot = SomeSpider()
    bot.setup_cache(backend='mongo', port=7777, host='mongo.localhost')


.. _spider_cache_compression:

Cache Compression
-----------------

By defalt cache compression is enabled. That means that all documents placed in
the cache are compressed with gzip libary. Compression decreases the disk space
required to store the cache and increases the CPU load (a bit).
