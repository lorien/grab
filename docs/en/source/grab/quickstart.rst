.. _grab_quickstart:

Grab Quickstart
===============

Before working with Grab ensure that you have a latest version of Grab. The
recommended way of installing Grab to you system is using pip utility::

    pip install -U Grab

Also you should manually install lxml and pycurl libraries.

Let's get started with simple examples.

Make a request
--------------

First, you need to import Grab class::

    >>> from grab import Grab

Then you can build Grab instance and make simple network request::

    >>> from grab import Grab
    >>> g = Grab()
    >>> resp = g.go('http://livejournal.com/') 

Now, we have a `Response` object which provides interface to response's content, cookies, headers and other things.

We've just made a GET requests. To make reqests of other type you need to configure
Grab instance via `setup` method with `method` option::

    >>> g.setup(method='put')
    >>> g.setup(method='delete')
    >>> g.setup(method='options')
    >>> g.setup(method='head') 

Let's see small example of HEAD request::

    >>> g = Grab()
    >>> g.setup(method='head')
    >>> resp = g.go('http://google.com/robots.txt')
    >>> print len(resp.body)
    0
    >>> print resp.headers['Content-Length']
    1776

Creating POST requests
----------------------

When you build site scrapers or work with network APIs it is a common task to create
POST requests. You can build POST request using `post` option::

    >>> g = Grab()
    >>> g.setup(post={'username': 'Root', 'password': 'asd7DD&*ssd'})
    >>> g.go('http://example.com/log-in-form')

Another common task is to get a web form, fill it and submit it. Grab provides
API to work with forms::

    >> g = Grab()
    >> g.go('http://example/com/log-in')
    >> g.set_input('username', 'Foo')
    >> g.set_input('password', 'Bar')
    >> g.submit()

Then you call `submit` method Grab build POST request with values which you've
passed with `set_input` methods. If you did not specify values for some form's
elements then Grab use their default values.

Grab also provide interface to upload files::

    >>> from grab import Grab, UploadFile
    >>> g = Grab()
    >>> g.setup(post={'name': 'Flower', 'file': UploadFile('/path/to/image.png')})
    >>> g.submit()

Also you can upload files via form API::

    >>> from grab import Grab, UloadFile
    >>> g = Grab()
    >>> g.go('http://example.com/some-form')
    >>> g.set_input('name', 'A flower')
    >>> g.set_input('file', UploadFile('/path/to/image.png'))
    >>> g.submit()

Response Content
----------------

Consider the simple page retreiving code again::

    >>> g = Grab()
    >>> resp = g.go('http://google.com/')

To get response content as unicode use::

    >>> resp.unicode_body()

Note that grab automatically detect the charset of response content and convert
it to the unicode. You can get detected charset with::

    >>> resp.charset

If you need original response body then use::

    >>> resp.body

Oiriginal content is useful if you need to save some binary content like image:::

    >>> resp = g.go('http://example.com/some-log.png')
    >>> open('logo.png', 'w').write(resp.body)

The `gzip` and `deflate` encodings are automatically decoded.

Response Status Code
--------------------

TO BE CONTINUED
