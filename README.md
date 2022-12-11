# Grab Framework Project

[![Grab Test Status](https://github.com/lorien/grab/actions/workflows/test.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Code Quality](https://github.com/lorien/grab/actions/workflows/check.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Type Check](https://github.com/lorien/grab/actions/workflows/mypy.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/mypy.yml)
[![Grab Test Coverage Status](https://coveralls.io/repos/github/lorien/grab/badge.svg)](https://coveralls.io/github/lorien/grab)
[![Grab Documentation](https://readthedocs.org/projects/grab/badge/?version=latest)](https://grab.readthedocs.io/en/latest/)

## Project Status

Important notice: pycurl backend is dropped. The only network transport now is urllib3.

The project is in a slow refactoring stage. It might be possible there will not be new features.

Things that are going to happen (no estimation time):

* Refactoring the source code while keeping most of the external API unchanged
* Fixing bugs
* Annotating source code with type hints
* Improving the quality of source code to comply with pylint and other linters
* Moving some features into external packages or moving external dependencies inside Grab
* Fixing memory leaks
* Improving test coverage
* Adding more platforms and python versions to test matrix
* Releasing new versions on pypi


## Installation

```
$ pip install -U grab
```

See details about installing Grab on different platforms here https://grab.readthedocs.io/en/latest/usage/installation.html


## Documentation

Documenations is here https://grab.readthedocs.io/en/latest/

Documentation for Grab version 0.6.41 (released in 2018 year) is here https://grab.readthedocs.io/en/v0.6.41-doc/

## About Grab (very old description)

Grab is a python web scraping framework. Grab provides a number of helpful methods
to perform network requests, scrape websites and process the scraped content:

* Automatic cookies (session) support
* HTTPS/SOCKS proxy support with/without authentication
* Keep-Alive support
* IDN support
* Tools to work with web forms
* Easy multipart file uploading
* Flexible customization of HTTP requests
* Automatic charset detection
* Powerful API to extract data from DOM tree of HTML documents with XPATH queries

Grab provides an interface called Spider to develop multithreaded website scrapers:

* Rules and conventions to organize crawling logic
* Multiple parallel network requests
* Automatic processing of network errors (failed tasks go back to a task queue)
* You can create network requests and parse responses with Grab API (see above)
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


## Community

Telegram English chat: [https://t.me/grablab](https://t.me/grablab)

Telegram Russian chat: [https://t.me/grablab\_ru](https://t.me/grablab_ru)
