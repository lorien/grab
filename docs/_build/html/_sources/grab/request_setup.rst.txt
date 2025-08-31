.. _grab_request_setup:

Setting up the Grab Request
===========================

To set up specific parameters of a network request you need to build the Grab
object and configure it. You can do both things at the same time:

.. code:: python

    g = Grab(url='http://example.com/', method='head', timeout=10)
    g.request()

Or you can build the Grab object with some initial settings and configure it 
later: 

.. code:: python

    g = Grab(timeout=10)
    g.setup(url='http://example.com', method='head')
    g.request()

Also you can pass settings as parameters to `request` or `go`:

.. code:: python

    g = Grab(timeout=10)
    g.setup(method='head')
    g.request(url='http://example.com')
    # OR
    g.request('http://example.com')

`request` and `go` are almost same except for one small thing. You do not
need to specify the explicit name of the first argument with `go`. The first
argument of the `go` method is always `url`. Except for this, all other named
arguments of `go` and `request` are just passed to the `setup` function.

For a full list of available settings you can check :ref:`grab_settings`


Grab Config Object
------------------

Every time you configure a Grab instance, all options are saved in the 
special object, `grab.config`, that holds all Grab instance settings. You can 
receive a copy of the config object and also you can setup a Grab instance 
with the config object: 

.. code:: python

    >>> g = Grab(url='http://google.com/')
    >>> g.config['url']
    'http://google.com/'
    >>> config = g.dump_config()
    >>> g2 = Grab()
    >>> g2.load_config(config)
    >>> g2.config['url']
    'http://google.com/'

The Grab config object is simply a `dict` object. Some of the values may also
be a `dict`.


.. _grab_configuration_cloning:

Grab Instance Cloning
---------------------

If you need to copy a Grab object there is a more elegant way than using the
`dump_config` and `load_config` methods:

.. code:: python

    g2 = g1.clone()

`g2` gets the same state as `g1`. In particular, `g2` will have the same 
cookies.  
