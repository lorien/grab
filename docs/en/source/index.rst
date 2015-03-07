Grab documentation
==================

Grab is a python framework for building web scrapers. The Grab consists of two
main parts:

1) Grab - API to create single network request and process result of response.
2) Grab::Spider - API to create crawler i.e. class that contains methods (handlers)
to process each spawned network request. Grab:Spider allows you to spawn
asynchronous network requests.

When to use Grab API:

* If you want just to send one single network request and process the response
* In most cases when you think to use urllib, urllib2, pycurl or requests libs.

When to use Grab:Spider API:

* If you want to extract data from a web site and you need to process pages
  of different types and you need to spawn multiple parallel network requests.
* In most cases when you think about of using scrapy.

Grab is not only a tool to build network requests and download network responses, it is also a tool to handle the data of network responses and extract information you need. Grab provides a flexible API to query parts of the DOM trees of HTML documents.

See the quick start tutorials to quickly get an overview of how to use Grab and Grab::Spider.

Grab User Manual
----------------

.. toctree::
    :maxdepth: 2

    grab_quickstart
    grab_installation
    grab_configuration
    grab_debugging
    grab_options
    grab_http_headers
    grab_http_methods
    grab_response_body
    grab_redirect
    grab_network_errors
    grab_forms
    grab_charset
    grab_cookies
    grab_proxy
    grab_response_search
    pycurl
    changelog
    grab_response
    grab_what_is_inside

API Reference
-------------

Using the API Reference you can get an overview of what modules, classes, and methods exist, what they do, what they return, and what parameters they accept.

Base Grab Interface
~~~~~~~~~~~~~~~~~~~

.. toctree::
    :maxdepth: 2

    api_grab_base
    api_grab_error
    api_grab_cookie
