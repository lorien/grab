Grab documentation
==================

Grab is a python framework for building site scrapers. The Grab library consists of two main interfaces:

1) Grab. The main interface to configure network requests and to handle network responses.
2) Grab::Spider. A more complex interface to build asynchronous site scrapers. The Spider interface has many commonalities with the Scrapy interface. The main benefits of Spider are an asynchronous concurrent request engine, and an internal design that forces you to organize scraping logic in to well structured blocks.

When to consider using the Grab API:

* When you want to submit a single network request and process the response
* In most cases when you think to use urllib, urllib2, pycurl or requests libs.

When Grab::Spider will probably be useful:

* When you need to extract data from a web site with multiple concurrent web workers
* In most cases when you are thinking of using scrapy.

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


Tools Package
~~~~~~~~~~~~~

.. toctree::
    :maxdepth: 3

    api_tools_html
    api_tools_work
    api_tools_pwork
    api_tools_lock
    api_tools_logs
    api_tools_files
    api_tools_lxml_tools
    api_tools_rex
    api_tools_text
    api_tools_http
    api_tools_content
    api_tools_control
    api_tools_debug
    api_tools_encoding
    api_tools_feed
    api_tools_metric
    api_tools_parser
    api_tools_russian
    api_tools_progress
    api_tools_user_agent
    api_tools_watch
    api_tools_system
