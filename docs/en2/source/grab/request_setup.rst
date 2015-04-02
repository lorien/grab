.. _grab_request_setup:

Setting up the Grab Request
===========================

To set up parameters of network request you need to build Grab
object and configure it. You can do both things in same time:

.. code:: python

    g = Grab(url='http://example.com/', method='head', timeout=10,
             user_agent='grab')
    g.request()

Or you can build Grab object with some initial settings and configure it later:

.. code:: python

    g = Grab(timeout=10, user_agent='grab')
    g.setup(url='http://example.com', method='head')
    g.request()

Also you can pass settings as parameters to `request` or `go` method:

.. code:: python

    g = Grab(timeout=10)
    g.setup(method='head')
    g.request(url='http://example.com', user_agent='grab')
    # OR
    g.go('http://example.com', user_agent='grab')

Methods `request` and `go` are almost same except one small thing. You do not
need to specify the explicit name of first argument of `go` method. First
argument of `go` method is always `url`. Except this thing all other named
arguments of `go` and `request` are just passed to `setup` function.

Full list of available settings you can see in :ref:`grab_settings`


Grab Config Object
------------------

Every time you configure a Grab instance, all options go to the special object
`grab.config` that holds all Grab instance settings. You can receive a copy of
the config object and also you can setup a Grab instance with the config object:

.. code:: python

    >>> g = Grab(url='http://google.com/')
    >>> g.config['url']
    'http://google.com/'
    >>> config = g.dump_config()
    >>> g2 = Grab()
    >>> g2.load_config(config)
    >>> g2.config['url']
    'http://google.com/'

The Grab config object is simply a `dict` object some of which values are also
`dict` objects.


.. _grab_configuration_cloning:

Grab Instance Cloning
---------------------

If you need to copy a Grab object there is a more elegant way than using
`dump_config` and `load_config` methods:

.. code:: python

    g2 = g1.clone()

Instance `g2` gets the same state as instance `g1`. In particular, `g2` gets
same cookies.

There is also `adopt`, which does the opposite of the `clone` method:

.. code:: python

    g2.adopt(g1)

The `g2` instance receives the state of `g1` instance.


.. _grab_configuration_pycurl:

Setting Up the Pycurl Object
----------------------------

Sometimes you need more detailed control of network requests than Grab allows.
In such cases you can configure the pycurl object directly. All Grab's network
features are only the interface to the pycurl library. Any available Grab
option just sets some option of the pycurl object. Here is a simple example of
how to change the type of the HTTP authentication:

.. code:: python

    >>> import pycurl
    >>> from grab import Grab
    >>> g = Grab()
    >>> g.setup(userpwd='root:123')
    >>> g.transport.curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
