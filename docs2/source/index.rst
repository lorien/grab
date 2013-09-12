Grab documentation
==================

Grab is a python framework for building site scrapers. Grab helps you to configure and submit network request and to extract data from network response. Grab library consists of two main interfaces:

1) Grab: this is the main interface to configure network requests and to handel network response.
2) Grab::Spider: this is more complex interface to build asynchronous site scrapers. Spider interface has many common with Scrapy interface. The main benefits of Spider is asynchronous concurrent request engine, network cache system, clean and structured source code of site scraper.

You need to use Grab API:

* When you want to submit network request and process the response
* Inside Grab::Spider to configure complex network request
* Inside Grab::Spider to work with data in network response 

You need Grab::Spider API:

* When you need to exract data from web site with multiple concurrent web workers

You can just think of Grab and Spider from this point: Grab is like a Requests library and Grab::Spider is like a Scrapy library. Good news, you can use Grab inside Grab::Spider to configure network requests as you want.

Grab is not only a tool to build network requests and download network responses, it is also a tool to parse data of network response and extract information you need. Grab provides great API to query parts of DOM-tree of the HTML document.

See quick start documetns to quickly get main ideas about how to use Grab:

* :ref:`grab_quickstart`
* :ref:`spider_quickstart`

.. toctree::
   :maxdepth: 2
