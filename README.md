# Grab Framework Project

[![Grab Test Status](https://github.com/lorien/grab/actions/workflows/test.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Code Quality](https://github.com/lorien/grab/actions/workflows/check.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Type Check](https://github.com/lorien/grab/actions/workflows/mypy.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/mypy.yml)
[![Grab Test Coverage Status](https://coveralls.io/repos/github/lorien/grab/badge.svg)](https://coveralls.io/github/lorien/grab)
[![Grab Documentation](https://readthedocs.org/projects/grab/badge/?version=latest)](https://grab.readthedocs.io/en/latest/)

## Status of Project

I myself have not used Grab for many years. I am not sure it is being used by anybody at present time.
Nonetheless I work on the project from time to time, just for fun. In 2022 I have annotated
whole Grab code base with type hints, it complies mypy in strict mode. Also the whole code base complies to
pylint and flake8 linters. There are few exceptions: very large methods and classes with too many local
atributes and variables. I will refactor them eventually. Also I have set up running mypy, pylint, flake8
and pytest in github actions.

Initially Grab worked with pycurl as network backend. Then I have added urllib3 backend. At present time
pycurl backend is not supported anymore.

I do not care if the project is not used anymore by anybody. I feel good by making Grab source code less shitty.
And, for sure, Grab source code is very shitty. And design is shitty too. I have created it many years ago.

Grab requires python of version 3.8 or higher.

## Thinks to be done next

* Refactor source code to remove all pylint disable comments like:
    * too-many-instance-attributes
    * too-many-arguments
    * too-many-locals
    * too-nany-lines
    * too-many-public-methods
* Make 100% test coverage, it is about 90% now
* Release new version to pypi


## Installation

```
$ pip install -U grab
```

See details about installing Grab on different platforms here https://grab.readthedocs.io/en/latest/usage/installation.html


## Documentation

Documenations is located here https://grab.readthedocs.io/en/latest/

Documentation for old Grab version 0.6.41 (released in 2018 year) is here https://grab.readthedocs.io/en/v0.6.41-doc/

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

## Deprecated Usage Examples

Following examples were written many years ago. In those times many of websites could
be scraped with bare network and html libraries, without using browser engines. I guess
following examples do not work anymore.


## Grab Usage Example

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

## Grab::Spider Usage Example

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
