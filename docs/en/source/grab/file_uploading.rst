.. _grab_file_uploading:

File Uploading
==============

To upload file you should use `UploadFile` or `UploadContent` classes.

UploadFile example:

.. code:: python

    from grab import Grab, UploadFile

    g = Grab()
    g.setup(post={'image': UploadFile('/path/to/image.jpg')})
    g.go('http://example.com/form.php')


UploadContent example:

.. code:: python

    from grab import Grab, UploadContent

    g = Grab()
    g.setup(post={'image': UploadContent('......', filename='image.jpg')})
    g.go('http://example.com/form.php')


.. _grab_file_uploading_form:

Form Processing
---------------

You can use `UploadFile` and `UploadContent` in all methods that set values in
form fields:

.. code:: python

    
    from grab import Grab, UploadContent

    g = Grab()
    g.go('http://example.com/form.php')
    g.doc.set_input('image', UploadFile('/path/to/image.jpg'))
    g.doc.submit()


.. _grab_file_uploading_custom_name:

Custom File Name
----------------

With both `UploadFile` and `UploadContent` you can use custom filename.

If you do not specify filename then:

* `UploadFile` will use the filename extracted from the path to the file passed in first argument.
* `UploadContent` will generate random file name

.. code:: python

    >>> from grab import UploadFile, UploadContent
    >>> UploadFile('/path/to/image.jpg').filename
    'image.jpg'
    >>> UploadFile('/path/to/image.jpg', filename='avatar.jpg').filename
    'avatar.jpg'
    >>> UploadContent('.....').filename
    '528e418951'
    >>> UploadContent('.....', filename='avatar.jpg').filename
    'avatar.jpg'


.. _grab_file_uploading_custom_content_type:

Custom Content Type
----------------

With both `UploadFile` and `UploadContent` you can use custom content type.

If you do not specify content type then lately the pycurl (the Grab network
request engine) will choose the content type by analizing the filename, but at
the time of creation upload object the content type will be just `None`.

.. code:: python

    >>> from grab import UploadFile, UploadContent
    >>> print(UploadFile('/path/to/image.jpg').content_type)
    None
    >>> UploadFile('/path/to/image.jpg', content_type='text/plain').content_type
    'text/plain'
    >>> print(UploadContent('/path/to/image.jpg').content_type)
    None
    >>> UploadContent('...', content_type='text/plain').content_type
    'text/plain'
