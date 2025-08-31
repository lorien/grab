.. Grab documentation master file, created by
   sphinx-quickstart on Tue Nov  9 11:04:59 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
.. _home:

Grab - фреймворк для парсинга сайтов
====================================

.. warning::

    Документация на русском языке устарела и может содержать ошибки.
    Пожалуйста, используйте английскую документацию для получения
    актуальной информации о библиотеке Grab.

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
* Репозиторий на github: http://github.com/lorien/grab
* Группа рассылки: http://groups.google.com/group/python-grab


.. _grab_toc:

Документация Grab
-----------------

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

Документация Grab:Spider
------------------------

Асинхронный модуль для разработки сложных парсеров.

.. toctree::
    :maxdepth: 2

    spider/tutorial
    spider/task_building
    spider/task
    spider/task_queue
    spider/error_handling
    spider/cache


API
---

Вся нижеследующая информация сгенерирована из комментариев в исходном коде.  Поэтому она на английском языке. Документы из раздела API полезны тем, что они показывают описания всех аргументов каждого метода и класса библиотеки Grab.

Базовый интерфейс:

.. toctree::
    :maxdepth: 2

    api/base
    api/error
    api/response

Утилиты:

.. toctree::
    :maxdepth: 2

    api/upload


Всякая фигня
------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
