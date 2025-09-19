.. _spider_transport:

Spider Transport
================

Spider transport is a component of Spider that controls network connections
i.e.  makes possible multiple network requests to run in parallel.

Multicurl transport
-------------------

This is default spider transport. It operates with multiple pycurl instances.
You can use only pycurl Grab transport with multicurl Spider transport.

..  code:: python

    from grab.spider import Spider, Task
    from grab import Grab
    import logging

    class SimpleSpider(Spider):
        def task_generator(self):
            yield Task('reddit', 'http://reddit.com')

        def task_reddit(self, grab, task):
            url = grab.doc('//p[contains(@class, "title")]/a/@href').text()
            # DO NOT DO THAT:
            # > g = Grab()
            # > g.go(url)
            # Do not use Grab directly
            # that will blocks all other parallel network requests
            # Only use `yield Task(...)`
            url = grab.make_url_absolute(url)
            yield Task('link', url=url)

        def task_link(self, grab, task):
            print('Title: %s' % grab.doc('//title').text())


    logging.basicConfig(level=logging.DEBUG)
    bot = SimpleSpider();
    bot.run()

Threaded transport
------------------

The threaded transport operates with a pool of threads. Network requests are
spread by these threads. You can use pycurl or urllib3 Grab transport with
threaded transport.

Grab can use two libraries to submit network requests: pycurl and urllib3. You may acess
transport object with `Grab.transport` attribute. In most cases you do not need direct
access to transport object.

.. code:: python

    from grab.spider import Spider, Task
    from grab import Grab
    import logging

    class SimpleSpider(Spider):
        def task_generator(self):
            yield Task('reddit', 'http://reddit.com')

        def task_reddit(self, grab, task):
            url = grab.doc('//p[contains(@class, "title")]/a/@href').text()
            # DO NOT DO THAT:
            # > g = Grab()
            # > g.go(url)
            # Do not use Grab directly
            # that will blocks all other parallel network requests
            # Only use `yield Task(...)`
            url = grab.make_url_absolute(url)
            yield Task('link', url=url)

        def task_link(self, grab, task):
            print('Title: %s' % grab.doc('//title').text())


    logging.basicConfig(level=logging.DEBUG)
    bot = SimpleSpider(transport='threaded', grab_transport='urllib3')
    # Also you can use pycurl Grab transport with threaded transport
    # bot = SimpleSpider(transport='threaded', grab_transport='pycurl')
    bot.run()
