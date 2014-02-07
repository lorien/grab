.. _grab_options:

===================
List of All Options
===================

To get info about how to setup Grab instance please go to :ref:`grab_configuration`.

Network options
===============

.. _option_url:

url
---

:Type: string
:Default: None

The URL of requested web page. You can use relative URLS, in that case Grab will build
the absolute url by joining the relative URL with the URL or previously requested document.
Be aware, that Grab does not automatically escapes the unsafe characters in the URL. This is a design feature. You can use `urllib.quote` and `urllib.quote_plus` functions to make your URLs safe.

More info about valid URLs is in `RFC 2396 <http://www.ietf.org/rfc/rfc2396.txt>`_.


.. _option_timeout:

timeout
-------

:Type: int
:Default: 15

Maximal time to network operation. If it exeeds the GrabNetworkTimeout is raised.


.. _option_connect_timeout:

connect_timeout
---------------

:Type: int
:Default: 3

Maximal time of operation of connection to remote server and getting initial response.
If it exeeds then the GrabNetworkTimeout is raised


.. _option_follow_refresh:

follow_refresh
--------------

:Type: bool
:Default: False

Automatically follow the URL specified in <meta http-equiv="refresh"> tag


.. _option_follow_location:

follow_location
---------------

:Type: bool
:Default: True

Automatically follow the location in 301/302 response.


.. _option_interface:

interface
---------

:Type: string
:Default: None

Network interface via that the request should be submitted.

To specify interface by its OS name use "if!***" format e.g. "if!eth0"
To specify interface by its name or ip address use "host!***" format e.g.
"host!127.0.0.1" or "host!localhost"

Also, check out pycurl manual: http://curl.haxx.se/libcurl/c/curl_easy_setopt.html#CURLOPTINTERFACE 


.. _option_redirect_limit:

redirect_limit
--------------

:Type: int
:Default: 10

Set the maximal number of redirects that Grab could do for one request. Redirects are following the "Location" header in 301/302 network responses and following the url specified in meta refresh tags.


.. _option_hammer_mode:

hammer_mode
-----------

:Type: bool
:Default: False

The special mode that forces Grab to repeat the network request in case of network error.
See details in :ref:`grab_hammer_mode`.


.. _option_hammer_timeouts:

hammer_timeouts
---------------

:Type: list
:Default: ((2, 5), (5, 10), (10, 20), (15, 30))

Settings of timeouts in hammer mode.


.. _option_userpwd:


userpwd
-------

:Type: string
:Default: None

The username and the password  to pass HTTP authorization. THe value of that options is the string of format "username:password".


HTTP Options
============

.. _option_user_agent:

user_agent
----------

:Type: string
:Default: see below

The content of "User-Agent" HTTP-header. By-default, Grab randomly chooses a user agent
from the list of real user agents that is built into Grab package.


.. _option_user_agent_file:

user_agent_file
---------------

:Type: string
:Default: None

Path to the text file with User-Agent strings. If that options is specified then
grab randomly choose one line from that file.


.. _option_method:

method
------

:Type: string
:Default: "GET"
:Possible values: "GET", "POST", "PUT", "DELETE"

The method of HTTP-request. By default, the GET method is used. If you specify `post` or
`multipart_post` option then Grab automatically changes method to POST.


.. _option_post:

post
----

:Type: sequence of pairs or dict or string
:Default: None

Data to be send with POST request. Depends on the type of data the corresponding method
of handling that data is choosed. Default type of POST request is "application/x-www-form-ulencoded".

In case of `dict` or sequence of pairs the following alogo is applyed to each value:

* objects of `grab.upload.UploadFile` class are converted into pycurl structures
* unicode strings are converted into byte strings
* None values are converted into empty strings

If `post` value is just a string then it is placed into network request without any modification.


.. _option_multipart_post:

multipart_post
--------------

:Type: sequence of pairs or dict
:Default: None

Data to be send with POST request. This option forces the POST request to be
in "multipart/form-data" form.


.. _option_headers:

headers
-------


:Type: dict
:Default: None

Extra HTTP-headers. The value of that options will be joined with headers
that Grab generates by default. See details in :ref:`grab_http_headers`.


.. _option_common_headers:

common_headers
--------------

:Type: dict
:Default: None

By default, Grab generates some common HTTP headers to mimic the behaviour of real web browser.
If you have some troubles with these deafult headers then you can specify your own headers with
that option. Please note that the usual way to specify some heaer is to use :ref:`option_headers` option. See details in :ref:`grab_http_headers`.

.. _option_reuse_cookies:

reuse_cookies
-------------

:Type: bool
:Default: True

If that option is enabled then all cookies in each network response are remembered and
sent back in furher requests to the server.

.. _option_cookies:

cookies
-------

:Type: dict
:Default: None

Cookies to send to the server. If the option :ref:`option_reuse_cookies` is also enabled
then cookies from the `cookies` option will be joined with remembered cookies.


.. _option_cookiefile:

cookiefile
----------

:Type: string
:Defaul: None

Before each request Grab willl read cookies from that file and join them with remembered cookies. After each response Grab will save all cookies to that file.
Format of data in the file: JSON serialized dict.


.. _option_referer:

referer
-------

:Type: string
:Default: see below

The content of "Referer" HTTP-header. By default, Grab build this header with the URL
of previously requested document.


.. _option_reuse_referer:

reuse_referer
-------------

:Type: bool
:Default: True

If that options is enabled, then Grab uses URL of previously requested documen to build
the content of "Referer" HTTP header.


Proxy Options
=============

.. _option_proxy:

proxy
-----

:Type: string
:Default: None

The address of the proxy server in format of "domain:port" or "ip:port".


.. _option_proxy_userpwd:

proxy_userpwd
-------------

:Type: string
:Default: None

Security data to submit to the proxy if it requires authenication.
Forma of data is "username:password"

.. _option_proxy_type:

proxy_type
----------

:Type: string
:Default: None

Type of proxy server. Available values are "http", "socks4" and "socks5".

Response Processing Options
===========================

.. _option_encoding:

encoding
--------

:Type: string
:Default: "gzip"

List of methods that remote server could use to compress the conten of response. By default, the value of this options is "gzip". To disable any compression method pass the empty string to that option.


.. _option_charset:

charset
-------

.. warning::

    Tere is also document_charset option, WTF???

Charset of content of the response. By deefault, charset is detected automatically
If that process is failed you can speficy charset manually. The value of that option
will be used to convert body of the document to the unicode, to pass the content to lxml lib to
build the DOM tree and in the process of encoding non-ascii data in POST data.

:Type: string
:Default: None


.. _option_nobody:

nobody
------

:Type: bool
:Default: False

Ignoring the body of network response. When this option is enable the connection is
abandoned at the moment when remote server transfered all headers of response and
started transfer the body of the response. You can use this option with any HTTP method.


.. _option_body_maxsize:

body_maxsize
------------

:Type: int
:Default: None

The limit on the maximum size of data that should be received from the remote server.
If limit is reached the connection is abandoned and you can work with data that
were received so far.


.. _option_lowercased_tree:

lowercased_tree
---------------

:type: bool
:Default: False

Conver content of document to lowercase before passing it to the lxml library to build the DOM tree. This option does not affect on the content of `response.body` that always stores original data.


.. _option_strip_null_bytes:

strip_null_bytes
----------------

:Type: bool
:Default: True

Control the removing of null bytes from the body of HTML documents before it is passed to lxml library to build DOM tree. The lxml library stop processing HTML documents at the first places where it founds null byte. To avoid such issued Grab, by default, removes null bytes from the document body. This option does not affect on the content of `response.body` that always stores original data.


.. _option_body_inmemory:

body_inmemory
-------------

:Type: bool
:Default: True

Control the method of downloading the network response. By default, Grab download data into memory. In case of large file, you can set `body_inmemory=False` to download network response directly to the disk.


.. _option_storage_dir:

storage_dir
-----------

:Type: bool
:Default: None

If you use `body_inmemory=False`, then you have to specify the directory where Grab will save network requests.


.. _option_body_storage_filename:

body_storage_filename
---------------------

:Type: string
:Default: None

If you use `body_inmemory=False`, then you can let Grab automatically choose names for files where is save network responses. By default, Grab build randomly unique names for files. With the `body_storage_filename` options you can choose exactly file name to save response. Note, that Grab will save every response to that file, so you need to change the `body_storage_filename` option before each new request or set it to None to enable default randomly geneated file names.


.. _option_content_type:

content_type
------------

:Type: string
:Default: "html"
:Available values: "html" and "xml"

This option controls what lxml parser is used to process the body of the response. By default, html parsed is used. If you want to parse XML then you sometimes need to change this option to "xml" to force using XML parser that does not strip content of CDATA nodes.


.. _option_fix_special_entities:

fix_special_entities
--------------------

:Type: bool
:Default: True

Fix &#X; entities, where X between 128 and 160 Such entities are parsed by modern
browsers as windows-1251 entities independently of the real charset of
the document, If this option is True then such entities
will be replaced with correct unicode entitites e.g.: &#151; ->  &#8212;

Debugging
=========

.. _option_log_file:

log_file
--------

:Type: string
:Default: None

Path to the file where the body of recent network response will be saved.
See details at :ref:`grab_debugging_response_saving`.


.. _option_log_dir:

log_dir
-------

:Type: string
:Default: None

Directory to save content of each response. Each response will be saved to the unique file.
See details at :ref:`grab_debugging_response_saving`.


.. _option_verbose_logging:

verbose_logging
---------------

:Type: bool
:Default: False

That option enables the print to console all detailed debug info about each pycul action. Sometimes that could be useful.


.. _option_debug_post:

debug_post
----------

:Type: bool
:Default: False

Enable logging of content of POST requests.


