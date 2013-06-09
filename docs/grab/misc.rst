.. _misc:

==============
Other Features
==============

Response Body Limit
===================

You can disable response body processing with option :ref:`option_nobody`. The response body will be downloaded, the network connection will be interrupted immediately after receiving all http-headers of response.

Another option to control the response is :ref:`option_body_maxsize`. You can specify maximal amount of data to receive before the connection will be interrupted. When the specified number of bytes has been received, the connection is interruped, no exceptions are raised and all data that were received are available.


Response Compressing
====================

You can control the compressing with option :ref:`option_encoding`. By defaulth, the value of this option is "gzip", that means that Grab sends "Accept-Encing: gzip" header in all requests and automatically decompress gziped responses. If you want to receive uncompressed responses from the server then use empty value for the option :ref:`option_encoding`.


HTTP Authentication
===================

Use :ref:`option_userpwd` option to send HTTP authentication headers. The value of the option is the string in format "username:password".


Low Level Acces to Pycurl Object
=================================

If you need to use any pycurl feature that has not interface in Grab then you can access pycurl handler directly. Example::

    >>> from grab import Grab
    >>> import pycurl
    >>> g = Grab()
    >>> g.transport.curl.setopt(pycurl.RANGE, '100-200')
    >>> g.go('http://some/url')


HTTP 301 and 302 Redirects
==========================

By default, HTTP responses with 301 and 302 status codes are processed automatically, Grab automatically goes to the URL specified in "Location:" header::

    HTTP/1.1 301 Moved Permanently
    Content-Type: text/html
    Content-Length: 174
    Location: http://www.example.org/

Use option :ref:`option_follow_location` to disable automatically processing of 301/302 redirects.


Meta Refresh Redirect
=====================

The HTML page could contain special HTML meta tag which instructs web client to do redirect to specified URL::

    <meta http-equiv="Refresh" content="0; url=http://some/url" />

Grab can automatically process such meta tags. By default, this feature is disabled. You can turn it on with option :ref:`option_follow_refresh`.
