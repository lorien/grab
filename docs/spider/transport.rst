.. _spider_transport:

Explanation
===========

Previously Grab library has been supporint multiple options for spider and grab transports.
At current moment there are no options. Spider use only threaded transport. Grab uses only
urllib3 transport.

Spider transport is a component of Spider that controls network connections
i.e.  makes possible multiple network requests to run in parallel.

The threaded transport operates with a pool of threads. Network requests are
spread by these threads. You can use urllib3 Grab transport with
threaded transport.

At the moment Grab supports only one network library to send network requests: urllib3.
You may access transport object with `Grab.transport` attribute. In most cases you do not need direct
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
            url = grab.make_url_absolute(url)
            yield Task('link', url=url)

        def task_link(self, grab, task):
            print('Title: %s' % grab.doc('//title').text())


    logging.basicConfig(level=logging.DEBUG)
    bot = SimpleSpider(transport='threaded', grab_transport='urllib3')
    bot.run()
