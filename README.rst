====
Grab
====

.. image:: https://travis-ci.org/lorien/grab.png
    :target: https://travis-ci.org/lorien/grab


Grab is a python site scraping framework. Grab provides tons of helpful methods to scrape web sites
and to work with scraped content:

* Automatic cookies (session) support
* HTTP and SOCKS proxy with and without authorization
* Keep-Alive support
* IDN support
* Tools to work with web forms
* Easy multipart file uploading
* Flexible customization of HTTP requests
* Automatic charset detection
* Powerful API of extracting info from HTML documents with XPATH queries
* Asynchronous API to make thousands of simultaneous queries. This part of library called Spider and it is too big to even list its features in this README.
* Python 3 ready
* And much, much more
* Grab has written by the guy who is doing site scraping since 2005

Check out docs: https://github.com/lorien/grab/tree/master/docs2/source

I am working hard now (Sep 2013) to complete the documentation in English.

Example of Grab usage::

    from grab import Grab

    g = Grab()
    g.go('https://github.com/login')
    g.set_input('login', 'lorien')
    g.set_input('password', '***')
    g.submit()
    for elem in g.doc.select('//ul[@id="repo_listing"]/li/a'):
        print '%s: %s' % (elem.text(), elem.attr('href'))


Example of Grab::Spider usage::

    from grab.spider import Spider, Task
    import logging

    class ExampleSpider(Spider):
        def task_generator(self):
            for lang in ('python', 'ruby', 'perl'):
                url = 'https://www.google.com/search?q=%s' % lang
                yield Task('search', url=url)
        
        def task_search(self, grab, task):
            print grab.doc.select('//div[@class="s"]//cite').text()


    logging.basicConfig(level=logging.DEBUG)
    bot = ExampleSpider()
    bot.run()


Installation
============

Pip is recommended way to install Grab and its dependencies::

    $ pip install lxml
    $ pip install pycurl
    $ pip install grab

See details here https://github.com/lorien/grab/blob/master/docs2/source/grab_installation.rst


Documentation
=============

Russian docs: http://docs.grablib.org

English docs in progress: https://github.com/lorien/grab/tree/master/docs2/source

Mailing List (Ru/En languages): http://groups.google.com/group/python-grab/


Contribution
============

If you have found a bug or wish a new feature please open new issue on github:

* https://github.com/lorien/grab/issues


.. image:: https://d2weczhvl823v0.cloudfront.net/lorien/grab/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free

