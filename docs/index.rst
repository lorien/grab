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

Grab сайты
----------

* Официальный сайт: http://grablib.org
* Репозиторий на bitbucket: http://bitbucket.org/lorien/grab
* Группа рассылки: http://groups.google.com/group/python-grab



Разделы документации
--------------------

Руководство пользователя
~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
    :maxdepth: 2

    grab/tutorial
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

API
~~~

Вся нижеследующая информация сгенерирована из комментариев в исходном коде.  Поэтому она на английском языке. Документы из раздела API полезны тем, что они показывают описания всех аргументов каждого метода и класса библиотеки Grab.

Базовый интерфейс:

.. toctree::
    :maxdepth: 2

    api/base
    api/error
    api/response

Расширения:

.. toctree::
    :maxdepth: 2

    api/ext_form
    api/ext_text
    api/ext_lxml
    api/ext_django
    api/ext_soup
    api/ext_rex
    api/ext_pquery

Утилиты:

.. toctree::
    :maxdepth: 2

    api/tools_html
    



Похожие проекты
----------------

* `urllib <http://docs.python.org/library/urllib.html>`_ and `urllib2 <http://docs.python.org/library/urllib2.html>`_ - для суровых python-хакеров
* `Scrapy <http://scrapy.org>`_ - пожалуй, самый известный python фреймворк для парсинга сайтов
* `Mechanize <http://wwwsearch.sourceforge.net/mechanize/>`_ - одна из самых старых python-библиотек парсинга сайтов
* `Requests <http://docs.python-requests.org>`_ - простой интерфейс к стандартной urllib библиотеке


Всякая фигня
------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
