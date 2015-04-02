.. _grab_http_headers:

Work with HTTP Headers
======================

Custom headers
--------------

If you need to submit custom HTTP headers, you can specify any number of them
via :ref:`option_headers` option. A common case is to emulate an AJAX request::

    >>> g = Grab()
    >>> g.setup(header={'X-Requested-With': 'XMLHttpRequest'})

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

User-Agent header
-----------------

By default, for each request Grab randomly chooses one user agent from a
builtin list of real user agents. You can specify the exact User-Agent value with
the :ref:`option_user_agent` option. If you need to randomly choose user agents
from your own list of user agents, then you can put your list into a text file
and pass its location as :ref:`option_user_agent_file`.


Referer header
--------------

To specify the content of the Referer header, use the :ref:`option_referer`
option. By default, Grab use the URL of previously request document as value
of Referer header. If you do not like this behaviour, you can turn it off with
:ref:`option_reuse_referer` option.

HTTP Authentication
-------------------

To send HTTP authentication headers, use the :ref:`option_userpwd` option with
a value of the form "username:password".

