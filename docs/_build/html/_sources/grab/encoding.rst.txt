.. _grab_encoding:

HTML Document Encoding
======================

Why does encoding matter?
-------------------------

By default, Grab automatically detects the encoding of the body of the HTML document.
It uses this detected encoding to

* build a DOM tree
* convert the bytes from the body of the document into a unicode stream
* search for some unicode string in the body of the document
* convert unicode into bytes data, then some unicode data needs to be sent
  to the server from which the response was received.

The original content of the network response is always accessible with `response.body` attribute.
A unicode representation of the document body can be obtained by calling `response.unicode_body()`::

    >>> g.request('http://mail.ru/')
    <grab.response.Response object at 0x7f7d38af8940>
    >>> type(g.response.body)
    <type 'str'>
    >>> type(g.response.unicode_body())
    <type 'unicode'>
    >>> g.response.encoding
    'utf-8'

Encoding Detection Algorithm
----------------------------

Grab users https://github.com/lorien/unicodec library to detect encoding of the document. The unicodec library searches for
encoding in following sources (from most priority to less):

* BOM (byte order mark)

* Content-Type HTTP header::

    Content-Type: text/html; encoding=koi8-r

* HTML meta tag or XML declaration::
    
    <meta charset="utf-8">
    <meta name="http-equiv" content="text/html; encoding=cp1251" >
    <?xml version="1.0" encoding="UTF-8" standalone="no" ?>

    
If no source indicates the encoding, or if the found encoding has an invalid value, then grab falls back to a default of UTF-8.

Setting the encoding manually
-----------------------------

You can bypass automatic encoding detection and specify it manually with :ref:`option_encoding` option.
