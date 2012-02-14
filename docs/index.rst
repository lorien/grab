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

    grab/tutorial
    grab/customization
    grab/debugging
    grab/options
    grab/request

    extensions/overview
    extensions/form
    extensions/text
    extensions/django
    extensions/lxml
    configuration
    tools/html

* Руководство пользователя
    * :doc:`grab/tutorial`
    * :doc:`grab/customization`
    * :doc:`grab/debugging`
    * :doc:`grab/options`
    * :doc:`grab/request`

    * :doc:`extensions/overview`
    * :doc:`tools/html`

* API
    * :doc:`api/grab`
    * :doc:`extensions/form`
    * :doc:`extensions/text`
    * :doc:`extensions/django`
    * :doc:`extensions/lxml`

Grab links
==========

* Official site: http://grablib.org
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
