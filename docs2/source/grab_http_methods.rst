.. _grab_http_methods:

HTTP Methods
============

Choosing the HTTP Method
------------------------

By default, grab generates GET requests. If you specify one of :ref:`option_post` or :ref:`option_multipart_post` options, then Grab changes the method to POST. You can always explicily set the required method with :ref:`option_method` option::

    >>> g = Grab()
    >>> g.setup(method='put')
    >>> g.setup(method='delete')

To submit some data with PUT method, use both :ref:`option_post` and :ref:`option_method` options::

    >>> g = Grab()
    >>> g.setup(post={'some': 'data'}, method='put')


POST request
------------

Grab sets method to POST when you implicitly specify a POST data with one of :ref:`option_post` and :ref:`option_multipart_post` options, or when you explicitly use the :ref:`option_method` option. When :ref:`option_post` is used, Grab encodes POST data as "application/x-www-form-urlencoded". When :ref:`option_multipart_post` is used, Grab encodes data as "multipart/form-data".

You can pass data to :ref:`option_post` in multiple formats:

* if data is dict or a sequence of pairs, then it will be converted into a "key1=val1&key2=val2" string.
* if data is already a string, then it is not changed and is submitted as-is.


File submission
---------------

To submit a file, create an obect of special class `UploadFile` and put it into POST data::

    >>> from grab.upload import UploadFile
    >>> g = Grab()
    >>> g.setup(post={'some_file': UploadFile('/etc/passwd')})
