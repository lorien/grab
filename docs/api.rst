.. _api:

Interface of Grab
=================

Grab, extensions, transports, blah-blah

.. module:: grab.base

.. class:: BaseGrab

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
