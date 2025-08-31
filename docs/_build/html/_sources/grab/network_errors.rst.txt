.. _grab_network_errors:

Network Errors Handling
=======================

Network Errors
--------------

If a network request fails, Grab raises :py:class:`grab.error.GrabNetworkError`.
There are two situations when a network error exception will raise:

* the server broke connection or the connection timed out
* the response had any HTTP status code that is not 2XX or 404

Note particularly that 404 is a valid status code, and does not cause an exception to be raised.

Network Timeout
---------------

You can configure timeouts with the following options:

* connect to server timeout with :ref:`option_connect_timeout` option
* whole request/response operation timeout with :ref:`option_timeout` option

In case of a timeout, Grab raises :py:class:`grab.error.GrabTimeoutError`.
