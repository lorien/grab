# Grab Framework Documentation

![pytest status](https://github.com/lorien/grab/workflows/test/badge.svg)
[![coveralls](https://coveralls.io/repos/lorien/grab/badge.svg?branch=master)](https://coveralls.io/r/lorien/grab?branch=master)
[![documentation](https://readthedocs.org/projects/grab/badge/?version=latest)](http://docs.grablib.org/en/latest/)


## Installation

```shell

    $ pip install -U grab
```

See details about installing Grab on different platforms here http://docs.grablib.org/en/latest/usage/installation.html


## Support

Documentation: https://grablab.org/docs/

Russian telegram chat: https://t.me/grablab_ru

English telegram chat: https://t.me/grablab

To report bug please use GitHub issue tracker: https://github.com/lorien/grab/issues


## What is Grab?

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


## Grab Example

```python

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
```


## Grab::Spider Example

```python

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
```
