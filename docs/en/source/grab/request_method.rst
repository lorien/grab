.. _grab_request_method:

Request Methods
===============


You can make request of any HTTP method you need. By default Grab
makes GET request.

.. _grab_request_get:

GET Request
-----------

GET method is default request method.

.. code:: python

    g = Grab()
    g.go('http://example.com/')

If you need to pass arguments in query string, then you
have to build URL manually:

.. code:: python

    from urllib import urlencode

    g = Grab()
    qs = urlencode({'foo': 'bar', 'arg': 'val'})
    g.go('http://dumpz.org/?%s' % qs)

If your URL contains unsafe characters then you have to escape them
manually.

.. code:: python

    from urllib import quote

    g = Grab()
    url = u'https://ru.wikipedia.org/wiki/Россия'
    g.go(quote(url.encode('utf-8')))


.. _grab_request_post:

POST Request
------------

To make POST request you have to specify POST data with `post` option.
Usually, you will want to use dictionary value:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post={'foo': 'bar'})

You can pass unicode strings and numbers in values of `post` dict, they
will be converted to bytes string automatically. If you want to specify
charset that will be used to convert unicode to byte string, then use
`request_charset` option

.. code:: python

    g = Grab()
    g.go('http://example.com/', post={'who': u'конь в пальто'},
         charset='cp1251')

If the `post` option is a string then it is submitted in request as-is:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post='raw data')


If you want to pass multiple values with same key use the list of tuples:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post=[('key', 'val1'), ('key', 'val2')])

By default, Grab compose POST request with 'application/x-www-form-urlencoded` encoding method.
To enable `multipart/form-data` method use `post_multipart` method instead of
`post`:

.. code:: python

    g = Grab()
    g.go('http://example.com/', post_multipart=[('key', 'val1'),
                                                ('key', 'val2')])


To upload file use `grab.upload.UploadFile` class:

.. code:: python

    g = Grab()
    g.go('http://example.com/',
         post_multipart={'foo': 'bar', 'file': UploadFile('/path/to/file')})

.. _grab_request_put:

PUT Request
-----------

To make PUT request use both `post` and `method` options:

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
