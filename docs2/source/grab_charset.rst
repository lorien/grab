.. _grab_charset:

HTML Document Charset
=====================

Why charset matters?
--------------------

By default, Grab automatically detects charset of the body of the HTML document.
It uses detected charset for

* build a DOM tree
* convert bytes body of document into unicode stream
* search for some unicode string in the body of the document
* convert unicode into bytes data then some unicode data needs to be sent
  to the sever from that the response was received.

Original content of network response is always accessable at `response.body` attribute.
Unicode-representation of the docment body could received by calling to  `response.unicode_body()`::

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
    
If no source let know the charset or if found charset has invalid value then grab falls back to default UTF-8 charset.

Setting the charset manually
----------------------------

You can bypass automatic charset detection and specify it manually with :ref:`option_charset` option.
