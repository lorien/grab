.. _grab_response_body:

Processing the Response Body
============================

In this document, options related to processing the body of network response are discussed.

Partial Response Body Download
------------------------------

If you do not need the response body at all, use :ref:`option_nobody` option. When it is
enabled, Grab closes the network connection to the server right after it
receives all response headers from the server. This is not the same as sending a GET request. You can
submit a request of any type, e.g. POST, and not download the response body if you do not need it.

Another option to limit body processing is :ref:`option_body_maxsize`. It allows you to download
as many bytes of the response body as you need, and then closes the connection.

Note that neither of these options break the processing of the response into a Python object. In both cases you get a response object with a body attribute that contains only part of the response body data - whatever was received before connection interrupted.

Response Compression Method
---------------------------

You can control the compression of the server response body with :ref:`option_encoding`. The default value is "gzip". That means that Grab sends "Accept-Encoding: gzip" to the server, and if the server answers with a response body packed with gzip then Grab automatically unpacks the gzipped body, and you have unpacked data in the `response.body`. If you do not want the server to send you gziped data, use an empty string as the value of :ref:`option_encoding`.

