.. _api:

=================
Interface of Grab
=================

Grab is a set of core methods which could be extended by extensions.
By default grab instance initiated with three extensions: `grab.ext.pycurl`,
`grab.ext.lxml` and `grab.ext.lxml_form`. Some of grab extensions are called
`transports`. These extensions provide network functionality: setting up network library,
sending and receiving data. By default grab use `grab.ext.pycurl` extension. Also
`grab.ext.urllib` transport is available, but for now it does not support all grab features.

.. module:: grab.grab

.. class:: Grab()

    .. automethod:: __init__

    Available settings are listed in  :ref:`configuration`.

    Example::

        g = Grab(url='http://yandex.ru, timeout=1)
        resp = g.request()

    .. automethod:: reset

    .. automethod:: clone

    .. automethod:: setup

    See :ref:`configuration`.

    .. automethod:: go

    This is shortcut to ``request(url=url)``

    .. automethod:: request

    .. automethod:: search

    .. automethod:: assert_pattern

    .. automethod:: reload

    .. automethod:: repeat_request
