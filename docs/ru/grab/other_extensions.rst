=================
Другие расширения
=================

PyQuery расширение
==================

Через аттрибут :meth:`~grab.ext.pquery.PyqueryExtension.pyquery` вам доступен `PyQuery` объект, связанный с содержимым документа. `PyQuery <http://packages.python.org/pyquery/>`_ - это наслойка поверх lxml API, позволяющая выбирать элементы с помощью jQuery-селекторов::

    >>> g = Grab()
    >>> g.go('http://yandex.ru')
    <grab.response.Response object at 0x1159b10>
    >>> print g.pyquery('ol.b-news__news li:eq(0)')[0].text_content()
    1. Дальневосточники активно голосуют на выборах президента России

BeautifulSoup расширение
========================

Через аттрибут :meth:`~grab.ext.soup.BeautifulSoupExtension.soup` вы можете обращаться к DOM-дереву документа, через API BeautifulSoup. Обратите внимание, что это расширение не доступно по-умолчаню. Если оно вам нужно, создайте свой класс, унаследованный от классов `Grab` и :class:`grab.ext.soup.BeautifulSoupExtension`::

    >>> from grab.ext.soup import BeautifulSoupExtension
    >>> class MyGrab(Grab, BeautifulSoupExtension):
    ...     pass
    ... 
    >>> g = MyGrab()
    >>> g.go('http://yandex.ru')
    <grab.response.Response object at 0x13ea390>
    >>> g.soup.title
    <title>Яндекс</title>
