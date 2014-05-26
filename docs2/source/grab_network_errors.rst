..  _grab_network_errors:

Network Errors Handling
=======================

Network Errors
--------------

If network request fails Grab raise :py:class:`grab.error.GrabNetworkError` exception.
There are two cases when network error exception raises:

* server broke connection, connection timed out,
* any HTTP status code that is not 2XX or 404

Pay attention that 404 is valid status code and exception is not raised.

Network Timeout
---------------

You can configure timeouts with options:

* connect to server timeout with :ref:`option_connect_timeout` option
* whole request/response operation timeout with :ref:`option_timeout` option

In case of time out Grab raises :py:class:`grab.error.GrabTimeoutError` exception.
