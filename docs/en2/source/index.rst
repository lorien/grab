.. Grab documentation master file, created by
   sphinx-quickstart on Fri Mar 27 02:27:14 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Grab's documentation!
================================

Grab is python framework for building web scrapers. With Grab you can build web
scrapers of various complexity: from simple 5-line scripts to complex
asynchronous web-site crawlers processing millions of web pages. Grab provides
API for performing network requests and for handling received content e.g.
interacting with DOM tree of the HTML document.

There are two main parts in Grab library:

    1) The single request/response API that allows you build network request,
    perform it and work with the received content. That API is a wrapper
    of the pycurl and lxml libraries.

    2) The Spider API to build asynchronous web crawlers. You write class that
    define handlers for each type of network request. Each handler could spawn
    new network requests. Network requests are processed simultaneusly with a
    pool of asynchronous web sockets.


Table of Contents
=================

.. toctree::
    :maxdepth: 2

    usage/installation
    usage/testing
    grab/request_method
    grab/request_setup
    grab/settings



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
