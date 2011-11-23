.. Grab documentation master file, created by
   sphinx-quickstart on Tue Nov  9 11:04:59 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Grab
===============

Grab is python framework for writing site scrapers. Grab provides two interfaces:

 * the Grab interface for building HTTP request and processing response
 * the Spider interface for writing asynchronous site scrapers

Spider interface uses multicurl (the asynchronous pycurl interface). If you need to
do big number of concurrent requests then you should consider to use Spider. In
case of Grab interface you should write yourself the code which organizes the
concurrent network streams. In case of Spider it is already done in Spider module.
Anyway you should learn the Grab interface, because you will use it to construct
requests and to process results even in Spider based scrapers.

Documentation
-------------

.. toctree:
    :hidden:

    overview
    grab_tutorial
    spider_tutorial

:doc:`overview`
    List of features implemented in Grab

:doc:`grab_tutorial`
    Short lesson how to use Grab

:doc:`spider_tutorial`
    Rewriting the solution from previous tutorial with help of Spider framework

Grab links
----------

* Grab source code repository on bitbucket: http://bitbucket.org/lorien/grab
* Grab mailing list: http://groups.google.com/group/python-grab


Similar projects
----------------

* Scrapy - mature scraping solution: http://scrapy.org
* Mechanize - one of the oldest python scraping framework:
* Requests - easy interface to standard urllib library:
* Httplib2


Documenation sections
---------------------

.. toctree::
    :maxdepth: 2

    configuration
    forms


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
