====
Grab
====

.. image:: https://travis-ci.org/lorien/grab.png
    :target: https://travis-ci.org/lorien/grab


Grab is a python site scraping framework. Grab provides powerful interface to two libraries:
lxml and pycurl. There are two ways how to use Grab:
1) Use Grab to configure network requests and to process fetched documents. In this way you
should manually control flow of you program.
2) Use Grab::Spider to buld asynchronous site scrapers. This is how scrapy works.

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


Documentation
=============

Russian docs: http://docs.grablib.org
English docs in progress.

Discussion group (Russian or English): http://groups.google.com/group/python-grab/


Contribution
============

If you found a bug or if you want new feature please create new issue on github:

* https://github.com/lorien/grab/issues
