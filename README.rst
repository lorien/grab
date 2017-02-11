Grab
====

.. image:: https://travis-ci.org/lorien/grab.png?branch=master
    :target: https://travis-ci.org/lorien/grab?branch=master

.. image:: https://ci.appveyor.com/api/projects/status/uxj24vjin7gptdlg
    :target: https://ci.appveyor.com/project/lorien/grab

.. image:: https://coveralls.io/repos/lorien/grab/badge.svg?branch=master
    :target: https://coveralls.io/r/lorien/grab?branch=master

.. image:: https://api.codacy.com/project/badge/Grade/18465ca1458b4c5e99026aafa5b58e98
   :target: https://www.codacy.com/app/lorien/grab?utm_source=github.com&utm_medium=referral&utm_content=lorien/grab&utm_campaign=badger

.. image:: https://readthedocs.org/projects/grab/badge/?version=latest
    :target: http://docs.grablib.org/en/latest/


What is Grab?
-------------

Grab is a python web scraping framework. Grab provides a number of helpful methods
to perform network requests, scrape web sites and process the scraped content:

* Automatic cookies (session) support
* HTTP and SOCKS proxy with/without authorization
* Keep-Alive support
* IDN support
* Tools to work with web forms
* Easy multipart file uploading
* Flexible customization of HTTP requests
* Automatic charset detection
* Powerful API to extract data from DOM tree of HTML documents with XPATH queries
* Asynchronous API to make thousands of simultaneous queries. This part of
  library called Spider. See list of spider fetures below.
* Python 3 ready

Spider is a framework for writing web-site scrapers. Features:

* Rules and conventions to organize the request/parse logic in separate
  blocks of codes
* Multiple parallel network requests
* Automatic processing of network errors (failed tasks go back to task queue)
* You can create network requests and parse responses with Grab API (see above)
* HTTP proxy support
* Caching network results in permanent storage
* Different backends for task queue (in-memory, redis, mongodb)
* Tools to debug and collect statistics


Grab Example
------------

.. code:: python

    import logging

    from grab import Grab

    logging.basicConfig(level=logging.DEBUG)

    g = Grab()

    g.go('https://github.com/login')
    g.doc.set_input('login', '****')
    g.doc.set_input('password', '****')
    g.doc.submit()

    g.doc.save('/tmp/x.html')

    g.doc('//ul[@id="user-links"]//button[contains(@class, "signout")]').assert_exists()

    home_url = g.doc('//a[contains(@class, "header-nav-link name")]/@href').text()
    repo_url = home_url + '?tab=repositories'

    g.go(repo_url)

    for elem in g.doc.select('//h3[@class="repo-list-name"]/a'):
        print('%s: %s' % (elem.text(),
                          g.make_url_absolute(elem.attr('href'))))


Grab::Spider Example
--------------------

.. code:: python

    import logging

    from grab.spider import Spider, Task

    logging.basicConfig(level=logging.DEBUG)


    class ExampleSpider(Spider):
        def task_generator(self):
            for lang in 'python', 'ruby', 'perl':
                url = 'https://www.google.com/search?q=%s' % lang
                yield Task('search', url=url, lang=lang)

        def task_search(self, grab, task):
            print('%s: %s' % (task.lang,
                              grab.doc('//div[@class="s"]//cite').text()))


    bot = ExampleSpider(thread_number=2)
    bot.run()



Installation
------------

.. code:: bash

    $ pip install -U grab

See details about installing Grab on different platforms here http://docs.grablib.org/en/latest/usage/installation.html


Documentation and Help
----------------------

Documentation: http://docs.grablib.org/en/latest/

Mailing list (mostly russian): http://groups.google.com/group/python-grab/


Contribution
------------

To report a bug please use GitHub issue tracker: https://github.com/lorien/grab/issues

If you want to develop new feature in Grab please use issue tracker to
describe what you want to do or contact me at lorien@lorien.name
