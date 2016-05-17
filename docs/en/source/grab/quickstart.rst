.. _grab_quickstart:

Grab Quickstart
===============

Before working with Grab ensure that you have the latest version. The
recommended way of installing Grab is by using pip::

    pip install -U Grab

You should also manually install the lxml and pycurl libraries.

Let's get started with some simple examples.

Make a request
--------------

First, you need to import the Grab class::

    >>> from grab import Grab

Then you can build Grab instances and make simple network requests::

    >>> from grab import Grab
    >>> g = Grab()
    >>> resp = g.go('http://livejournal.com/') 

Now, we have a `Response` object which provides an interface to the 
response's content, cookies, headers and other things.  

We've just made a GET request. To make other request types, you need to
configure the Grab instance via the `setup` method with the `method` argument::

    >>> g.setup(method='put')
    >>> g.setup(method='delete')
    >>> g.setup(method='options')
    >>> g.setup(method='head') 

Let's see a small example of HEAD request::

    >>> g = Grab()
    >>> g.setup(method='head')
    >>> resp = g.go('http://google.com/robots.txt')
    >>> print len(resp.body)
    0
    >>> print resp.headers['Content-Length']
    1776

Creating POST requests
----------------------

When you build site scrapers or work with network APIs it is a common task to 
create POST requests. You can build POST request using the `post` option::

    >>> g = Grab()
    >>> g.setup(post={'username': 'Root', 'password': 'asd7DD&*ssd'})
    >>> g.go('http://example.com/log-in-form')

Another common task is to get a web form, fill it in and submit it. Grab 
provides an easy way to work with forms::

    >>> g = Grab()
    >>> g.go('http://example/com/log-in')
    >>> g.set_input('username', 'Foo')
    >>> g.set_input('password', 'Bar')
    >>> g.submit()

When you call `submit`, Grab will build a POST request using the values passed
in via `set_input`.  If you did not specify values for some form elements 
then Grab will use their default values.  

Grab also provides an interface to upload files::

    >>> from grab import Grab, UploadFile
    >>> g = Grab()
    >>> g.setup(post={'name': 'Flower', 'file': UploadFile('/path/to/image.png')})
    >>> g.submit()

Also you can upload files via the form API::

    >>> from grab import Grab, UloadFile
    >>> g = Grab()
    >>> g.go('http://example.com/some-form')
    >>> g.set_input('name', 'A flower')
    >>> g.set_input('file', UploadFile('/path/to/image.png'))
    >>> g.submit()

Response Content
----------------

Consider a simple page retrieving example::

    >>> g = Grab()
    >>> resp = g.go('http://google.com/')

To get the response content as unicode use::

    >>> resp.unicode_body()

Note that grab will automatically detect the character set (charset for 
short) of the response content and convert it to unicode. You can detected 
the charset with:: 

    >>> resp.charset

If you need the original response body then use::

    >>> resp.body

Original content is useful if you need to save a binary file (e.g. an image)::

    >>> resp = g.go('http://example.com/some-log.png')
    >>> open('logo.png', 'w').write(resp.body)

The `gzip` and `deflate` encodings are automatically decoded.

Response Status Code
--------------------

TO BE CONTINUED
