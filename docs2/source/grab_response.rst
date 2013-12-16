.. _grab_response:

Work With Network Response
==========================

Response Object
---------------

The result of doing network request via Grab is `Response` object.

You get response object as a result of calling to `g.go`, `g.request` and `g.submit` methods.
Also you can access to response object of recent network query via `g.response` attribute::

    >>> from grab import Grab
    >>> g = Grab()
    >>> g.go('http://google.com')
    <grab.response.Response object at 0x2cff9f0>
    >>> g.response
    <grab.response.Response object at 0x2cff9f0>

You can find full list of response attributes in Response API document. Here are the most
important things you should now:

:body: original body contents of HTTP response
:code: HTTP status of response
:headers: HTTP headers of response
:charset: charset of the response
:cookies: cookies in the response
:url: the URL of the response document. In case of some automatically processed redirect the
    `url` attribute contains the final URL.
:name_lookup_time: time spent to resolve host name
:connect_time: time spent to connect to remote server
:total_time: total time spent to complete the request
:download_size: size of received data
:upload_size: size of uploaded data except the HTTP headers

Now, real example::

    >>> from grab import Grab
    >>> g = Grab()
    >>> g.go('http://wikipedia.org')
    <grab.response.Response object at 0x1ff99f0>
    >>> g.response.body[:100]
    '<!DOCTYPE html>\n<html lang="mul" dir="ltr">\n<head>\n<!-- Sysops: Please do not edit the main template'
    >>> g.response.code
    200
    >>> g.response.headers['Content-Type']
    'text/html; charset=utf-8'
    >>> g.response.charset
    'utf-8'
    >>> g.response.cookies
    <grab.cookie.CookieManager object at 0x1f6b248>
    >>> g.response.url
    'http://www.wikipedia.org/'
    >>> g.response.name_lookup_time
    0.103931
    >>> g.response.connect_time
    0.221996
    >>> g.response.total_time
    0.7791399999999999
    >>> g.response.download_size
    11100.0
    >>> g.response.upload_size
    0.0

Now let's see some useful methods available in response object:

:unicode_body(): this method returns body of response converted to unicode
:copy(): returns clone of the response object
:save(path): saves response object to given location
:json: treats response content as json-serialized data and de-serializes it into python structure. Actually, this is not a method, it is a property.
:url_details(): return result of `urlparse.urlsplit` call with `response.url` as argument
:query_param(name): extracts value of `key` argument from query string of `response.url`
