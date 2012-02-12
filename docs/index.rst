.. Grab documentation master file, created by
   sphinx-quickstart on Tue Nov  9 11:04:59 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Документация по библиотеке Grab
===============================

Grab - библиотека для работы с сетевыми документами. Основные области использования Grab:

 * извлечение данных с веб-сайтов (site scraping)
 * работа с сетевыми API
 * автоматизация работы с веб-сайтами, например, регистратор профилей на каком-либо сайте

Grab состоит из двух частей:
 
 * Главный интерфейс Grab для создания сетевого запроса и работы с его результатом. Этот 
   интерфейс удобно использовать в простых скриптах, где не нужна большая многопоточность,
   или непосредственно в python-консоли.
 * Интерфейс Spider, позволяющий разрабатывать асинхронные парсеры. Этот интерфейс позволяет,
   во-первых, более строго описать логику парсера, во-вторых, разрабатывать парсеры с большим
   числом сетевых потоков.

Разделы документации
--------------------

.. toctree::
    :hidden:

    grab_tutorial
    grab_customization
    base_interface
    extensions/overview
    extensions/form
    extensions/text
    extensions/django
    extensions/lxml
    configuration
    tools/html

:doc:`grab_tutorial`
    Введение в Grab

:doc:`grab_customization`
    Создание и конфигурация Grab объекта.

:doc:`base_interface`
    Base Grab interface. The core functions.

:doc:`extensions/overview`
    Overview of grab functionality splitted by so-called extensions. 

    :doc:`extensions/form`
        Automated form processing

    mdoc:`extensions/text`
        Utilities to process text of response

    :doc:`extensions/django`
        Provides quick way to save response content into FileField of any django model.

    :doc:`extensions/lxml`
        Extracting information from response with XPATH and CSS queries.

:doc:`configuration`
    Configuring Grab instance. Configuring network request options.

Extra cool things

    :doc:`tools/html`
        HTML processing utilities
        

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
