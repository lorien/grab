.. _grab_configuration:

Configuration
=============

You can configure a Grab instance in multiple ways.

First, you can pass options to the Grab instance constructor::

    >>> g = Grab(timeout=10, url='http://yahoo.com/')

Also, you can use `setup` method - the most common way to set up a Grab instance::

    >>> g = Grab()
    >>> g.setup(timeout=10, url='http://yahoo.com/')

And finally, you can specify options as arguments of a method that triggers a network request.
There are two such methods: `go` and `request`. The only difference is that `request` has no positional
arguments, while `go` method has one positional argument for the `url` option::

    >>> g = Grab()
    >>> g.request(timeout=10, url='http://yahoo.com/')
    >>> # OR
    >>> g = Grab()
    >>> g.go('http://yahoo.com/', timeout=10)

You can mix ways of specifying the options::

    >>> g = Grab(timeout=10)
    >>> g.setup(cookies={'foo': 'bar'})
    >>> g.request(url='http://yahoo.com/')

.. _grab_configuration_config_object:


Grab Config Object
------------------

Every time you configure a Grab instance, all options go to the special object `grab.config` that holds all Grab instance settings. You can receive a copy of that config object and also you can setup a Grab instance with the config object::

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

If you need to copy a Grab object there is a more elegant way than using `dump_config` and `load_config` methods::

    >>> g2 = g1.clone()

That's all. Instance `g2` gets the same state as instance `g1`. In particular, `g2` gets the same cookies.

There is also `adopt`, which does the opposite of the `clone` method::

    >>> g2.adopt(g1)

The `g2` instance receives the state of `g1` instance.

.. _grab_configuration_pycurl:


Setting Up the Pycurl Object
----------------------------

Sometimes you need more detailed control of network requests than Grab allows. In such cases you can configure the pycurl object directly. All Grab's network features are only the interface to the pycurl library. Any available Grab option is just set some option of the pycurl object. Here is a simple example of how to change the type of the HTTP authentication::

    >>> import pycurl
    >>> from grab import Grab
    >>> g = Grab()
    >>> g.setup(userpwd='root:123')
    >>> g.transport.curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
