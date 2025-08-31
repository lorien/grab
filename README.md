# Grab

## Update (2025 year)

I have reset all project files to the state of recent pypi release dated by june 2018.

If you need most recent state of the project before reset, use commit tagged as "cancelled-refactoring".


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



## Installation

Run `pip install -U grab`

See details about installing Grab on different platforms here https://grab.readthedocs.io/en/stable/usage/installation.html


## Documentation and Help

Documentation: https://grab.readthedocs.io/en/stable/


## Bug Reports

To report a bug create new issue in https://github.com/lorien/grab/issues
