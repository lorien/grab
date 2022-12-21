.. _grab_http_headers:

Work with HTTP Headers
======================

Custom headers
--------------

If you need to submit custom HTTP headers, you can specify any number of them
via :ref:`option_headers` option. A common case is to emulate an AJAX request::

    >>> g = Grab()
    >>> g.setup(headers={'X-Requested-With': 'XMLHttpRequest'})

Bear in mind, that except headers in :ref:`option_headers` option (that is
empty by default) Grab also generates a bunch of headers to emulate a typical
web browser. At the moment of writing these docs these headers are:

* Accept
* Accept-Language
* Accept-Charset
* Keep-Alive
* Except

If you need to change one of these headers, you can override its value with the
:ref:`option_headers` option. You can also subclass the Grab class and define
your own `common_headers` method to completely override the logic of
generating these extra headers.
