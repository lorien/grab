.. Grab documentation master file, created by
   sphinx-quickstart on Fri Mar 27 02:27:14 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Grab's documentation!
================================

Useful Links
------------

* Source code: https://github.com/lorien/grab
* Documentation: https://grab.readthedocs.io/en/latest/
* Russian Web Scraping Chat Group: https://t.me/grablab_ru
* English Web Scraping Chat Group: https://t.me/grablab

What is Grab?
-------------

Grab is a python framework for building web scrapers. With Grab you can build 
web scrapers of various complexity, from simple 5-line scripts to complex
asynchronous website crawlers processing millions of web pages. Grab provides
an API for performing network requests and for handling the received content 
e.g.  interacting with DOM tree of the HTML document.

There are two main parts in the Grab library:

    1) The single request/response API that allows you to build network 
    request, perform it and work with the received content. The API is built
    on top of urllib3 and lxml libraries.

    2) The Spider API to build asynchronous web crawlers. You write classes 
    that define handlers for each type of network request. Each handler is able
    to spawn new network requests. Network requests are processed concurrently 
    with a pool of asynchronous web sockets.


Table of Contents
=================

.. _grab_toc:

Grab User Manual
----------------

.. toctree::
    :maxdepth: 2

    usage/installation
    usage/testing
    grab/quickstart
    grab/request_method
    grab/request_setup
    grab/settings
    grab/debugging
    grab/request_headers
    grab/redirect
    grab/forms
    grab/network_errors
    grab/encoding
    grab/cookies
    grab/proxy
    grab/response_search
    grab/response
    grab/transport


.. _spider_toc:

Grab::Spider User Manual
------------------------

Grab::Spider is a framework to build well-structured asynchronous web-site 
crawlers.  

.. toctree::
    :maxdepth: 2

    spider/intro
    spider/task
    spider/task_queue
    spider/error_handling
    spider/transport

..
    spider/proxy - new
    spider/stat - new (inc_count/add_item/save_list/render_stats/save_all_lists)


.. _api_toc:

API Reference
-------------

Using the API Reference you can get an overview of what modules, classes, and 
methods exist, what they do, what they return, and what parameters they accept.  

.. toctree::
    :maxdepth: 2

    autoapi/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
