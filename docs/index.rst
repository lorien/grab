.. Grab documentation master file, created by
   sphinx-quickstart on Tue Nov  9 11:04:59 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
.. _home:

Grab - Site Scraping Framework
==============================

Grab is site scraping framework. Grab could be used for:

 * website data mining
 * work with network API
 * automation of actions performed on websites i.e. creation of profile on some site

Grab consists of following parts:

 * Grab interface for creating network requests and working with results of these
   requests. This interface is good for simple scripts where is no need in multithreading.
 * Grab::Spider interface which allows to develop complex multithreaded asynchronous site scrapers. This interface has two main benefits:
   
  1. It restrict you spider to have clean structure
  2. It allows to perform multiple concurrent requests without big CPU/memory consumption


.. _grab_toc:

Grab User Guide
---------------

.. toctree::
    :maxdepth: 2

    grab/tutorial
    grab/installation
    grab/customization
    grab/debugging
    grab/options
    grab/http_headers
    grab/http_methods
    grab/misc
    grab/charset
    grab/cookies
    grab/errors
    grab/proxy
    grab/response
    grab/under_the_hood
    grab/forms
    grab/dom
    grab/text_search
    grab/other_extensions
    grab/transport
    grab/tools

.. _spider_toc:

Grab::Spider User Guide
-----------------------

.. toctree::
    :maxdepth: 2

    spider/tutorial
    spider/task_building
    spider/task
    spider/task_queue
    spider/error_handling
    spider/cache

TODO::

    * Работа с прокси
    * Утилиты:
     * process_links
     * process_next_page
     * inc_count/add_item/save_list/render_stats/save_all_lists
     * process_object_image
    


Grab API Reference
------------------

If you are looking for information on a specific function, class or method, this part of the documentation is for you.

Base Interface

.. toctree::
    :maxdepth: 2

    api/base
    api/error
    api/response

Extensions:

.. toctree::
    :maxdepth: 2

    api/ext_form
    api/ext_text
    api/ext_lxml
    api/ext_django
    api/ext_soup
    api/ext_rex
    api/ext_pquery

Tools:

.. toctree::
    :maxdepth: 2

    api/tools_html
    api/tools
    api/upload
