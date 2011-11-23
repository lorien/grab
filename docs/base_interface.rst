.. _base_interface:

Base Grab Interface
===================

Work with Grab consists of three-step iterations.

1. Configure grab (see :ref:`configuration`):
    * Pass options to Grab instance constructor
    * Pass options to `go` or `request` method
    * Pass options to `setup` method
    * Crate new Grab instance with `clone` method
2. Fire a network request:
    * Call `request` or `go` method
    * Call `submit` method of `grab.ext.form` extension
    * Call `download` method
3. Process response:
    * A lot of different methods. See :ref:`extensions_overview` documentation.

Base Grab API (public methods)
------------------------------

.. module:: grab.base

.. autoclass:: BaseGrab

    .. automethod:: __init__
    .. automethod:: reset
    .. automethod:: clone
    .. automethod:: setup
    .. automethod:: go
    .. automethod:: download
    .. automethod:: request
    .. automethod:: sleep
    .. automethod:: fake_response
    .. automethod:: setup_proxylist
    .. automethod:: change_proxy
    .. automethod:: make_url_absolute
    .. automethod:: clear_cookies
