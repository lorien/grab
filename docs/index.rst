.. Grab documentation master file, created by
   sphinx-quickstart on Tue Nov  9 11:04:59 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Grab
===============

Grab is python framework for writing site scrapers. Grab provides two interfaces:

 * the Grab interface for building HTTP request and processing response
 * the Spider interface for writing asynchronous site scrapers

Grab interface is very simple and it is ideal for small scripts, for single-thread
scripts or for network hacking via python console.

Spider interface is powered by multicurl (the asynchronous pycurl interface).
If you need to do big number of concurrent requests then you should consider 
to use Spider.


Documentation
=============

.. toctree::
    :hidden:

    overview
    grab_tutorial
    spider_tutorial
    extensions/overview
    configuration

:doc:`overview`
    List of features implemented in Grab

:doc:`grab_tutorial`
    Short lesson how to use Grab

:doc:`spider_tutorial`
    Rewriting the solution from previous tutorial with help of Spider framework

:doc:`extensions/overview`
    Overview of grab functionality splitted by so-called extensions. 

:doc:`configuration`
    Configuring Grab instance. Configuring network request options.

Grab links
==========

* Grab source code repository on bitbucket: http://bitbucket.org/lorien/grab
* Grab mailing list: http://groups.google.com/group/python-grab


Similar projects
================

* Scrapy - mature scraping solution: http://scrapy.org
* Mechanize - one of the oldest python scraping framework:
* Requests - easy interface to standard urllib library:
* Httplib2


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
