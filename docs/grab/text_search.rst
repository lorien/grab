.. _text_search:

========================
Поиск в тексте документа
========================

Поиск строк
===========

.. currentmodule:: grab.ext.text

Методом :meth:`~TextExtension.search` можно установить наличие или отсутствие текстового фрагмента в исходном коде документа. Обратите внимание, что поиск проводится именно в HTML-коде, а не в объединение текстового содержимого всех элементов документа.

Может оказаться полезным метод :meth:`~TextExtension.assert_substring`, единственное назначение которого выбросить :class:`~grab.error.DataNotFound` исключение, если искомая строка не найдена. Для проверки существования хотя бы одной строки из множества, можно использовать метод :meth:`~TextExtension.assert_substrings`.

По-умолчанию, описанные методы ожидают аргумент в unicode-виде и проводят поиск в :meth:`grab.response.Response.unicode_body`. Если вы хотите искать байтовую строку в :attr:`grab.response.Response.body`, передайте дополнительный аргумент `byte=True` в поисковый метод::

    >>> g.go('http://forum.omsk.com')
    <grab.response.Response object at 0x1910f10>
    >>> g.search(u'<title>')
    True
    >>> g.search(u'Омск')
    True
    >>> g.search('Омск')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/local/lib/python2.6/dist-packages/grab/ext/text.py", line 36, in search
        raise GrabMisuseError('The anchor should be byte string in non-byte mode')
    grab.error.GrabMisuseError: The anchor should be byte string in non-byte mode
    >>> g.search(u'Омск'.encode('cp1251'), byte=True)
    True    

Поиск регулярных выражений
==========================

.. currentmodule:: grab.ext.rex

Метод :meth:`~RegexpExtension.rex` позволяет искать регулярное выражение в исходном коде документа. В качестве аргумента вы можете передать либо уже скомпилированный объект регулярного выражения либо текстовую строку, которая будет скомпилирована в объект регулярного выражения автоматически.

Если вам нужно извлечь из исхоного кода некоторый фрагмент, может оказаться полезным метод :meth:`~RegexpExtension.rex_text`, который ищет регулярное выражение и возвращает первую группу из него::

    >>> g.go('http://linode.com')
    <grab.response.Response object at 0x20a8150>
    >>> g.rex(re.compile('<title>[^>]+</title>')).group(0)
    u'<title>Linode - Xen VPS Hosting</title>'
    >>> g.rex('<title>[^>]+</title>').group(0)
    u'<title>Linode - Xen VPS Hosting</title>'
    >>> g.rex_text('<title>([^>]+)</title>')
    u'Linode - Xen VPS Hosting'

Метод :meth:`~RegexpExtension.assert_rex` по принципу действия аналогичен методу :meth:`~grab.ext.text.TextExtension.assert_substring`.
