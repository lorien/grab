.. _grab_charset:

HTML Document Charset
=====================

Why does charset matter?
------------------------

By default, Grab automatically detects the charset of the body of the HTML document.
It uses this detected charset to

* build a DOM tree
* convert the bytes from the body of the document into a unicode stream
* search for some unicode string in the body of the document
* convert unicode into bytes data, then some unicode data needs to be sent
  to the server from which the response was received.

The original content of the network response is always accessible at `response.body` attribute.
A unicode representation of the document body can be obtained by calling `response.unicode_body()`::

    >>> g.go('http://mail.ru/')
    <grab.response.Response object at 0x7f7d38af8940>
    >>> type(g.response.body)
    <type 'str'>
    >>> type(g.response.unicode_body())
    <type 'unicode'>
    >>> g.response.charset
    'utf-8'

Charset Detection Algorithm
---------------------------

Grab checks multiple sources to find out the real charset of the document's body. The order of sources (from most important to less):

* HTML meta tag::
    
    <meta name="http-equiv" content="text/html; charset=cp1251" >

* XML declaration (in case of XML document)::

    <?xml version="1.0" encoding="UTF-8" standalone="no" ?>

* Content-Type HTTP header::

    Content-Type: text/html; charset=koi8-r
    
If no source indicates the charset, or if the found charset has an invalid value, then grab falls back to a default of UTF-8.

Setting the charset manually
----------------------------

You can bypass automatic charset detection and specify it manually with :ref:`option_charset` option.
