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
