# Grab

## Update (2025 year)

Since 2018 (which is the year of most recent Grab release) I have tried to do large refactoring of
code base of Grab library. Which ended up with semi-working product which nobody uses, including me.
I have decided to reset all project files to the state of most recent pypi release 0.6.41 dated by june 2018.
At least, now the code base corresponds to live version of the product which is being used by some people,
according to [pypi stats](https://clickpy.clickhouse.com/dashboard/grab).

I've updated Grab code base and code base of its dependencies to be compatible with Python 2.7 and Python 3.13
(and, hopefully, all py versions between these two). I have set up github action to run all tests on Python 2.7
and Python 3.13.

There is NO new features. It is just an updated code base which is alive now i.e. it can run on Python 2.7 or on
modern python, and its tests pass, and it has github CI config to run tests on new commits.

One backward-incompatible change is that I do not use `weblib.error::DataNotFound` and `weblib.error::ResponseNotValid`
exceptions anymore. Now Grab uses DataNotFound and InvalidResponseError exceptions which is stored in `grab.errors` module.
So, if your code imports `DataNotFound` or `ResponseNotValid` from weblib, you should fix such imports. Also, if
your code explicitly catches these weblib exceptions then you should convert it to catch new `grab.error` exceptions.

The new release has version 1.0.0. If you use Grab in your project and you want to keep old release to be sure
there is no backward-compatility bugs, then use this specification in your requirements file  `grab<1.0`.


## Support

You are welcome to talk about web scraping and data processing in these Telegram chat groups: [@grablab](https://t.me/grablab) (English) and [@grablab\_ru](https://t.me/grablab_ru) (Russian)

Documentation: https://grab.readthedocs.io/en/stable/


## Installation

Run `pip install -U grab`

See details about installing Grab on different platforms here https://grab.readthedocs.io/en/stable/usage/installation.html


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
