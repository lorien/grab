.. _grab_response_search:

Searching the response body
===========================

String search
-------------

With the `doc.text_search` method, you can find out if the response body contains a certain string or not::

    >>> g = Grab('<h1>test</h1>')
    >>> g.doc.text_search(u'tes')
    True

If you prefer to raise an exception if string was not found, then use the `doc.text_assert` method::

    >>> g = Grab('<h1>test</h1>')
    >>> g.doc.text_assert(u'tez')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/lorien/web/grab/grab/document.py", line 109, in text_assert
        raise DataNotFound(u'Substring not found: %s' % anchor)
    grab.error.DataNotFound: Substring not found: tez

All text search methods understands both str and bytes queries. If you search for str the document
body converted to str is used. If you search for bytes the original bytes document body is used.


Regexp Search
-------------

You can search for a regular expression with `doc.rex_search` method that accepts compiled regexp object or just a text of regular expression::

    >>> g = Grab('<h1>test</h1>')
    >>> g.doc.rex_search('<.+?>').group(0)
    u'<h1>'

Method `doc.rex_text` returns you text contents of `.group(1)` of the found match object::

    >>> g = Grab('<h1>test</h1>')
    >>> g.doc.rex_text('<.+?>(.+)<')
    u'test'
    

Method `doc.rex_assert` raises `DataNotFound` exception if no match is found::

    >>> g = Grab('<h1>test</h1>')
    >>> g.doc.rex_assert('\w{10}')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/lorien/web/grab/grab/document.py", line 189, in rex_assert
        self.rex_search(rex)
      File "/home/lorien/web/grab/grab/document.py", line 180, in rex_search
        raise DataNotFound('Could not find regexp: %s' % regexp)
    grab.error.DataNotFound: Could not find regexp: <_sre.SRE_Pattern object at 0x7fa40e97d1f8>
