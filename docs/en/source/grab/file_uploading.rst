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
