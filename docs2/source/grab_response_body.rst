.. _grab_response_body:

Processing of Response Body
===========================

In this document options related to processing body of network response are discussed.

Partial Response Body Download
------------------------------

If you do not need body of response at all, use :ref:`option_nobody` option. When it is
enabled the Grab breaks network connection to the server right after when it has received
all headers of server's response. This is not the same as to send GET request. You can
submit request of any type, e.g. POST, and do not download resonse body if you do not need it.

Another option to limit body processing is :ref:`option_body_maxsize`. It allows you to download
as much as you need bytes of response body and the breaks connection.

Note, that both these options do not break the processing of the respons. In both cases you got
response object with body attribute that contains only part of the response body data that has been received before connection interrupted.

Response Compressing Method
---------------------------

You can control the compression of server response body with :ref:`option_encoding`. By default, the value of it is "gzip". That means that Grab sends "Accept-Encoding: gzip" to the server, and if server answers with body of response packed with gzip algorith then Grab automatically unpuck the gziped body and you have unpucked data in the `response.body`. If you do not want server sends you gziped data, use empty string as :ref:`option_encoding` value.
