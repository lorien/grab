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


.. _option_follow_refresh:

follow_refresh
^^^^^^^^^^^^^^

:Type: bool
:Default: False

Automatically follow the URL specified in <meta http-equiv="refresh"> tag.


.. _option_follow_location:

follow_location
^^^^^^^^^^^^^^^

:Type: bool
:Default: True

Automatically follow the location in 301/302 response.


.. _option_interface:

interface
^^^^^^^^^

:Type: string
:Default: None

The network interface through which the request should be submitted.

To specify the interface by its OS name, use "if!***" format, e.g. "if!eth0".
To specify the interface by its name or ip address, use "host!***" format, e.g.
"host!127.0.0.1" or "host!localhost".

See also the pycurl manual: http://curl.haxx.se/libcurl/c/curl_easy_setopt.html#CURLOPTINTERFACE


.. _option_redirect_limit:

redirect_limit
^^^^^^^^^^^^^^

:Type: int
:Default: 10

Set the maximum number of redirects that Grab will do for one request.
Redirects follow the "Location" header in 301/302 network responses, and
also follow the URL specified in meta refresh tags.


.. _option_userpwd:


userpwd
^^^^^^^

:Type: string
:Default: None

The username and the password to send during HTTP authorization. The value of that options is the string of format "username:password".


HTTP Options
------------

.. _option_user_agent:

user_agent
^^^^^^^^^^

:Type: string
:Default: see below

Sets the content of the "User-Agent" HTTP-header. By default, Grab randomly chooses a user agent
from the list of real user agents that is built into Grab itself.


.. _option_user_agent_file:

user_agent_file
^^^^^^^^^^^^^^^

:Type: string
:Default: None

Path to the text file with User-Agent strings. If this option is specified, then
Grab randomly chooses one line from that file.


.. _option_method:

method
^^^^^^

:Type: string
:Default: "GET"
:Possible values: "GET", "POST", "PUT", "DELETE"

The HTTP request method to use. By default, GET is used. If you specify `post` or
`multipart_post` options, then Grab automatically changes the method to POST.


.. _option_post:

post
^^^^

:Type: sequence of pairs or dict or string
:Default: None

Data to be sent with the POST request. Depending on the type of data, the corresponding method
of handling that data is selected. The default type for POST requests is "application/x-www-form-urlencoded".

In case of `dict` or sequence of pairs, the following algorithm is applied to each value:

* objects of `grab.upload.UploadFile` class are converted into pycurl structures
* unicode strings are converted into byte strings
* None values are converted into empty strings

If `post` value is just a string, then it is placed into the network request without any modification.


.. _option_multipart_post:

multipart_post
^^^^^^^^^^^^^^

:Type: sequence of pairs or dict
:Default: None

Data to be sent with the POST request. This option forces the POST request to be
in "multipart/form-data" form.


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
:Defaul: None

Before each request, Grab will read cookies from this file and join them with stored cookies. After each response, Grab will save all cookies to that file.
The data stored in the file is a dict serialized as JSON.


.. _option_referer:

referer
^^^^^^^

:Type: string
:Default: see below

The content of the "Referer" HTTP-header. By default, Grab builds this header with the URL
of the previously requested document.


.. _option_reuse_referer:

reuse_referer
^^^^^^^^^^^^^

:Type: bool
:Default: True

If this option is enabled, then Grab uses the URL of the previously requested document to build
the content of the "Referer" HTTP header.


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
:Default: "gzip"

List of methods that the remote server could use to compress the content of its response. The default value of this option is "gzip". To disable all
compression, pass the empty string to this option.


.. _option_document_charset:

document_charset
^^^^^^^^^^^^^^^^

:Type: string
:Default: None

The character set of the document's content.
By default Grab detects the charset of the document automatically. If it detects the charset incorrectly you can specify exact charset with this option.
The charset is used to get unicode representation of the document content and also to build DOM tree.

.. _option_charset:

charset
^^^^^^^

:Type: string
:Default: 'utf-8'

To send a request to the network Grab should convert all unicode data into bytes. It uses the `charset` for encoding. For example:

.. code:: python

    g.setup(post=b'abc')
    
no conversion required. But if

.. code:: python

    g.setup(post='Превед, медвед!')
    
then the unicode data has to be converted to `charset` encoding. By default that would be utf-8.

.. _option_nobody:

nobody
^^^^^^

:Type: bool
:Default: False

Ignore the body of the network response. When this option is enabled, the connection is
abandoned at the moment when remote server transfers all response headers and
begins to transfer the body of the response. You can use this option with any HTTP method.


.. _option_body_maxsize:

body_maxsize
^^^^^^^^^^^^

:Type: int
:Default: None

A limit on the maximum size of data that should be received from the remote server.
If the limit is reached, the connection is abandoned and you can work with the data 
received so far.


.. _option_lowercased_tree:

lowercased_tree
^^^^^^^^^^^^^^^

:type: bool
:Default: False

Convert the content of the document to lowercase before passing it to the lxml library to build the DOM tree.
This option does not affect the content of `response.body`, which always stores the original data.


.. _option_strip_null_bytes:

strip_null_bytes
^^^^^^^^^^^^^^^^

:Type: bool
:Default: True

Control the removal of null bytes from the body of HTML documents before they a re passed to lxml to build a DOM tree.
lxml stops processing HTML documents at the first place where it finds a null byte. To avoid such issues Grab,
removes null bytes from the document body by default. This option does not affect the content of `response.body` that always stores the original data.


.. _option_body_inmemory:

body_inmemory
^^^^^^^^^^^^^

:Type: bool
:Default: True

Control the way the network response is received. By default, Grab downloads data into memory.
To handle large files, you can set `body_inmemory=False` to download the network response directly to the disk.


.. _option_body_storage_dir:

body_storage_dir
^^^^^^^^^^^

:Type: bool
:Default: None

If you use `body_inmemory=False`, then you have to specify the directory where Grab will save network requests.


.. _option_body_storage_filename:

body_storage_filename
^^^^^^^^^^^^^^^^^^^^^

:Type: string
:Default: None

If you use `body_inmemory=False`, you can let Grab automatically choose names for the files where it saves network responses.
By default, Grab randomly builds unique names for files. With the `body_storage_filename` option, you can choose the
exact file name to save response to. Note that Grab will save every response to that file, so you need to change
the `body_storage_filename` option before each new request, or set it to None to enable default randomly generated file names.


.. _option_content_type:

content_type
^^^^^^^^^^^^

:Type: string
:Default: "html"
:Available values: "html" and "xml"

This option controls which lxml parser is used to process the body of the response. By default, the html parser is used.
If you want to parse XML, then you may need to change this option to "xml" to force the use of an XML parser which does not strip the content of CDATA nodes.


.. _option_fix_special_entities:

fix_special_entities
^^^^^^^^^^^^^^^^^^^^

:Type: bool
:Default: True

Fix &#X; entities, where X between 128 and 160. Such entities are parsed by modern
browsers as windows-1251 entities, independently of the real charset of
the document. If this option is True, then such entities
will be replaced with appropriate unicode entities, e.g.: &#151; ->  &#8212;

Debugging
---------

.. _option_log_file:

log_file
^^^^^^^^

:Type: string
:Default: None

Path to the file where the body of the recent network response will be saved.
See details at :ref:`grab_debugging_response_saving`.


.. _option_log_dir:

log_dir
^^^^^^^

:Type: string
:Default: None

Directory to save the content of each response in. Each response will be saved to a unique file.
See details at :ref:`grab_debugging_response_saving`.


.. _option_verbose_logging:

verbose_logging
^^^^^^^^^^^^^^^

:Type: bool
:Default: False

This option enables printing to console of all detailed debug info about each pycurl action. Sometimes this can be useful.


.. _option_debug_post:

debug_post
^^^^^^^^^^

:Type: bool
:Default: False

Enable logging of POST request content.
