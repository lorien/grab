Grab
====

.. image:: https://travis-ci.org/lorien/grab.png?branch=master
    :target: https://travis-ci.org/lorien/grab?branch=master

.. image:: https://coveralls.io/repos/lorien/grab/badge.svg?branch=master
    :target: https://coveralls.io/r/lorien/grab?branch=master

.. image:: https://img.shields.io/pypi/dm/grab.svg
    :target: https://pypi.python.org/pypi/grab

.. image:: https://img.shields.io/pypi/v/grab.svg
    :target: https://pypi.python.org/pypi/grab

.. image:: https://readthedocs.org/projects/grab/badge/?version=latest
    :target: http://docs.grablib.org/en/latest/


What is Grab?
-------------

Grab is a python web scraping framework. Grab provides tons of helpful methods
to scrape web sites and to process the scraped content:

* Automatic cookies (session) support
* HTTP and SOCKS proxy with and without authorization
* Keep-Alive support
* IDN support
* Tools to work with web forms
* Easy multipart file uploading
* Flexible customization of HTTP requests
* Automatic charset detection
* Powerful API of extracting info from HTML documents with XPATH queries
* Asynchronous API to make thousands of simultaneous queries. This part of
  library called Spider and it is too big to even list its features
  in this README.
* Python 3 ready


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

        @staticmethod
        def task_search(grab, task):
            print('%s: %s' % (task.lang,
                              grab.doc('//div[@class="s"]//cite').text()))


    bot = ExampleSpider(thread_number=2)
    bot.run()



Installation
------------

Pip is recommended way to install Grab and its dependencies:

.. code:: bash

    $ pip install -U grab

See details here http://docs.grablib.org/en/latest/usage/installation.html


Documentation and Help
----------------------

Documentation: http://docs.grablib.org/en/latest/

English mailing list: http://groups.google.com/group/grab-users/

Russian mailing list: http://groups.google.com/group/python-grab/


Contribution
============

To report a bug please use GitHub issue tracker: https://github.com/lorien/grab/issues

If you want to develop new feature in Grab please use issue tracker to
describe what you want to do or contact me at lorien@lorien.name
