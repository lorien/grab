.. _grab_settings:

Grab Settings
=============

Network options
---------------

.. _option_url:

url
^^^

:Type: string
:Default: None

The URL of the requested web page. You can use relative URLS, in which case Grab will build
the absolute url by joining the relative URL with the URL or previously requested document.
Be aware that Grab does not automatically escape unsafe characters in the URL.
This is a design feature. You can use `urllib.quote` and `urllib.quote_plus` functions to make your URLs safe.

More info about valid URLs is in `RFC 2396 <http://www.ietf.org/rfc/rfc2396.txt>`_.


.. _option_timeout:

timeout
^^^^^^^

:Type: int
:Default: 15

Maximum time for a network operation. If it is exceeded, GrabNetworkTimeout is raised.


.. _option_connect_timeout:

connect_timeout
^^^^^^^^^^^^^^^

:Type: int
:Default: 3

Maximum time for connection to the remote server and receipt of an initial
response. If it is exceeded, GrabNetworkTimeout is raised.


.. _option_process_redirect:

process_redirect
^^^^^^^^^^^^^^^

:Type: bool
:Default: True

Automatically process HTTP 30* redirects.


.. _option_redirect_limit:

redirect_limit
^^^^^^^^^^^^^^

:Type: int
:Default: 10

Set the maximum number of redirects that Grab will do for one request.
Redirects follow the "Location" header in 301/302 network responses, and
also follow the URL specified in meta refresh tags.


.. _option_method:

method
^^^^^^

:Type: string
:Default: "GET"
:Possible values: "GET", "POST", "PUT", "DELETE"

The HTTP request method to use. By default, GET is used. If you specify `post` or
`multipart_post` options, then Grab automatically changes the method to POST.


.. _option_post:

fields
^^^^^^

:Type: sequence of pairs or dict
:Default: None

Data to be sent in serialized form. Serialization depends on the type of request.
For GET on mulitpart post requests the "urlencode" method is used.
By default POST/PUT requests are multipart.

.. _option_multipart:

multipart
^^^^^^^^^

:Type: boolean
:Default: True

Control if multipart encoding must be used for PUT/POST requests.


.. _option_multipart_post:

body
^^^^

:Type: bytes
:Default: None

Raw bytes content to send


.. _option_headers:

headers
^^^^^^^


:Type: dict
:Default: None

Additional HTTP-headers. The value of this option will be added to headers
that Grab generates by default. See details in :ref:`grab_http_headers`.


.. _option_common_headers:

common_headers
^^^^^^^^^^^^^^

:Type: dict
:Default: None

By default, Grab generates some common HTTP headers to mimic the behaviour of a real web browser.
If you have trouble with these default headers, you can specify your own headers with
this option. Please note that the usual way to specify a header is to use the :ref:`option_headers` option. See details in :ref:`grab_http_headers`.

.. _option_reuse_cookies:

reuse_cookies
^^^^^^^^^^^^^

:Type: bool
:Default: True

If this option is enabled, then all cookies in each network response are stored
locally and sent back with further requests to the same server.

.. _option_cookies:

cookies
^^^^^^^

:Type: dict
:Default: None

Cookies to send to the server. If the option :ref:`option_reuse_cookies` is also enabled,
then cookies from the `cookies` option will be joined with stored cookies.


.. _option_cookiefile:

cookiefile
^^^^^^^^^^

:Type: string
:Default: None

Before each request, Grab will read cookies from this file and join them with stored cookies. After each response, Grab will save all cookies to that file.
The data stored in the file is a dict serialized as JSON.


Proxy Options
-------------

.. _option_proxy:

proxy
^^^^^

:Type: string
:Default: None

The address of the proxy server, in either "domain:port" or "ip:port" format.


.. _option_proxy_userpwd:

proxy_userpwd
^^^^^^^^^^^^^

:Type: string
:Default: None

Security data to submit to the proxy if it requires authentication.
Form of data is "username:password"

.. _option_proxy_type:

proxy_type
^^^^^^^^^^

:Type: string
:Default: None

Type of proxy server. Available values are "http", "socks4" and "socks5".

.. _option_proxy_auto_change:

proxy_auto_change
^^^^^^^^^^^^^^^^^

:Type: bool
:Default: True

If Grab should change the proxy before every network request.

Response Processing Options
---------------------------

.. _option_encoding:

encoding
^^^^^^^^

:Type: string
:Default: None

The encoding (character set) is used to store document's content as bytes.
By default Grab detects encoding of document automatically. If it detects the encoding incorrectly you can specify exact encoding with this option.
The encoding option is used to convert document's bytes content into Unicode text also for biilding DOM tree of the document.


.. _option_content_type:

content_type
^^^^^^^^^^^^

:Type: string
:Default: "html"
:Available values: "html" and "xml"

This option controls which lxml parser is used to process the body of the response. By default, the html parser is used.
If you want to parse XML, then you may need to change this option to "xml" to force the use of an XML parser which does not strip the content of CDATA nodes.


Debugging
---------
