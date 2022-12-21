.. _grab_response_body:

Processing the Response Body
============================

In this document, options related to processing the body of network response are discussed.

Partial Response Body Download
------------------------------

If you do not need the response body at all, use :ref:`option_body_maxsize` option.  When it is
set to zero, Grab closes the network connection to the server right after it
receives all response headers from the server. This is not the same as sending a GET request. You can
submit a request of any type, e.g. POST, and not download the response body if you do not need it.

With non zero values of :ref:`option_body_maxsize` option you can control how many bytes of document to
download before cancelling request.

By using this option you do not break the normal flow of request/response processing i.e. you will get
Response object as usual. It is just its body will contains only partial bytes of response.
