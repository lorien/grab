.. _grab_http_headers:

Work with HTTP Headers
======================

Custom headers
--------------

If you need to submit custom HTTP header you can specify any number of headers via
:ref:`option_headers` option. The common case is to emulate AJAX request::

    >>> g = Grab()
    >>> g.setup(header={'X-Requested-With': 'XMLHttpRequest'})

Bear in mind, that except headers in :ref:`option_headers` option (that is empty by default) Grab
generates also a bunch of headers to emulate typical web browser. At the moment of writing these docs these headers are:

* Accept
* Accept-Language
* Accept-Charset
* Keep-Alive
* Except

If you need to change one of these headers you can override its value with :ref:`option_headers` option. Also you can subclass Grab class and define you own `common_headers` method to completely override the logic of generation these extra headers.

User-Agent header
-----------------

By default, for each request Grab randomly choose one user agent from the builtin list of real user agents. You can specify exact User-Agent value with :ref:`option_user_agent` option. If you need to randomly choose user agents from your own list of user agent then you can put your list into a text file and the pass its location in :ref:`option_user_agent_file`.


Referer header
--------------

To specify content of Referer header use :ref:`option_referer` option. By default, Grab use the URL of previously request document as value of Referer header. If you do not like this behaviour, you can turn it off with :ref:`option_reuse_referer` option.

HTTP Authentication
-------------------

To send HTTP authentication headers use :ref:`option_userpwd` option with value of format "username:password".
