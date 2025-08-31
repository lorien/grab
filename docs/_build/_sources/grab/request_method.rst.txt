.. _grab_request_method:

Request Methods
===============


You can make any type of HTTP request you need. By default Grab will make a
GET request.

.. _grab_request_get:

GET Request
-----------

GET is the default request method.

.. code:: python

    g = Grab()
    g.go('http://example.com/')

If you need to pass arguments in through the query string, then you
have to build the URL manually:

.. code:: python

    from urllib import urlencode

    g = Grab()
    qs = urlencode({'foo': 'bar', 'arg': 'val'})
    g.go('http://dumpz.org/?%s' % qs)

If your URL contains unsafe characters then you must escape them manually.

.. code:: python

    from urllib import quote

    g = Grab()
    url = u'https://ru.wikipedia.org/wiki/Россия'
    g.go(quote(url.encode('utf-8')))


.. _grab_request_post:

POST Request
------------

To make a POST request you have to specify POST data with the `post` option.
Usually, you will want to use a dictionary:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post={'foo': 'bar'})

You can pass unicode strings and numbers in as values for the `post` dict, 
they will be converted to byte strings automatically. If you want to specify a
charset that will be used to convert unicode to byte string, then use
`request_charset` option.

.. code:: python

    g = Grab()
    g.go('http://example.com/', post={'who': u'конь в пальто'},
         charset='cp1251')

If the `post` option is a string then it is submitted as-is:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post='raw data')


If you want to pass multiple values with the same key use the list of tuples
version:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post=[('key', 'val1'), ('key', 'val2')])

By default, Grab will compose a POST request with 
'application/x-www-form-urlencoded` encoding method. To enable 
`multipart/form-data` use the `post_multipart` argument instead of `post`:

.. code:: python

    g = Grab()
    g.go('http://example.com/', multipart_post=[('key', 'val1'),
                                                ('key', 'val2')])


To upload a file, use the `grab.upload.UploadFile` class:

.. code:: python

    g = Grab()
    g.go('http://example.com/',
         multipart_post={'foo': 'bar', 'file': UploadFile('/path/to/file')})

.. _grab_request_put:

PUT Request
-----------

To make a PUT request use both the `post` and `method` arguments:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post='raw data', method='put')


.. _grab_request_other:

Other Methods
-------------

To make DELETE, OPTIONS and other HTTP requests, use the `method` option.

.. code:: python

    g = Grab()
    g.go('http://example.com/', method='options')
