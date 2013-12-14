.. _dom:

.. currentmodule:: grab.ext.lxml

====================
Работа с DOM-деревом
====================

Интерфейс к LXML библиотеке
===========================

Первое, что вам нужно усвоить, это то, что Grab предоставляет всего лишь удобный интерфейс к функциям библиотеки `lxml <http://lxml.de>`_. Крайне желательно, знать и понимать API библиотеки lxml. Grab предоставляет множество функций поиска данных в документе. Большинство этих функций представляют из себя xpath-запрос к DOM-дереву и последующую его обработку.

Далее описаны основные принципы использования lxml-расширения. Полный список методов (и их описание) вы можете посмотреть в API справочнике :ref:`extensions_lxml`.

DOM-дерево
==========

DOM-дерево доступно через аттрибут :meth:`tree <LXMLExtension.tree`::

    >>> g.go('http://vk.com')
    <grab.response.Response object at 0x1c9ae10>
    >>> g.tree
    <Element html at 1c96940>
    >>> print g.tree.xpath('//title/text()')[0]
    Welcome!
    
Вычисление DOM-дерева требует значительных ресурсов процессора, поэтому оно не вычисляется сразу после получения тела документа, а лишь только при первом вызове какого-либо xpath/css метода или обращении к аттрибуту :meth:`tree <LXMLExtension.tree`. DOM-дерево вычисляется один раз и затем кэшируется.


XPATH-методы
============

Самый часто используемый метод, это :meth:`~LXMLExtension.xpath`. В качестве аргумента он принимает xpath-выражение и возвращает найденный узел DOM-дерева. Пожалуйста, не путайте :meth:`~LXMLExtension.xpath` метод объекта Grab и `xpath` метод `lxml.html.etree.Element` объекта. Последний возвращает список элементов, в то время как `xpath` метод Grab-объекта возвращает первый найденный элемент. Если вам нужен список объектов, используйте :meth:`~LXMLExtension.xpath_list` метод. Приведу наглядный пример::

    >>> g.go('http://google.com')
    <grab.response.Response object at 0x1ae73d0>
    >>> g.xpath_list('//*[@type="submit"]')
    [<InputElement 1a35e88 name='btnG' type='submit'>, <InputElement 1c96530 name='btnI' type='submit'>]
    >>> g.xpath('//*[@type="submit"]')
    <InputElement 1a35e88 name='btnG' type='submit'>
    >>> from lxml.html import fromstring
    >>> fromstring(g.response.body).xpath('//*[@type="submit"]')
    [<InputElement 1c966d0 name='btnG' type='submit'>, <InputElement 1c96598 name='btnI' type='submit'>]    

Методом `xpath_text` вы можете извлечь текстовое содержимое из найденного DOM-элемента. Метод `xpath_number` извлекает в начале текстовое содержимое, затем ищет там число::

    >>> g.go('http://rambler.ru')
    <grab.response.Response object at 0x1c9a650>
    >>> print g.xpath_text('//td[@class="Spine"]//nobr')
    1996—2012
    >>> print g.xpath_number('//td[@class="Spine"]//nobr')
    1996

CSS-методы
==========

Благодаря модулю `cssselect <http://lxml.de/cssselect.html>`_, можно искать элементы в DOM-дереве с помощью CSS-выражений. Поддерживаются основные CSS2-селекторы, не все. Список и название методов для работы с CSS аналогичен списку методов для работы с xpath.

    >>> g.go('http://rambler.ru')
    <grab.response.Response object at 0x1c9a650>
    >>> print g.css_text('td.Spine nobr')
    1996—2012
    >>> print g.css_number('td.Spine nobr')
    1996

Обработка исключений
====================

Если xpath/css метод не нашёл данных, то генерируется исключение :class:`~grab.error.DataNotFound`. Класс этого ислючения унаследован от :class:`IndexError`, так что можно просто ловить IndexError на заморачиваясь на импорт `DataNotFound` исключения::

    >>> try:
    ...     g.xpath('//foobar')
    ... except IndexError:
    ...     print 'not found'
    ... 
    not found

Все xpath/css методы понимают аргумент `default`, если вы зададите его, то в случае, когда данные не были найден, вместо генерации исключения, xpath/css метод вернёт указанное значение. В качестве значения вы можете передавать даже `None`::

    >>> print g.xpath('//foobar')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/local/lib/python2.6/dist-packages/grab/ext/lxml.py", line 134, in xpath
        raise DataNotFound('Xpath not found: %s' % path)
    grab.error.DataNotFound: Xpath not found: //foobar
    >>> print g.xpath('//foobar', default=None)
    None
    >>> print g.xpath('//foobar', default='spam')
    spam
