.. _api_grab_cookie:

.. module:: grab.cookie

Module grab.cookie
==================

This module contains some classes to work with cookies.

.. autofunction:: create_cookie

.. autoclass:: CookieManager

    .. automethod:: __init__
    .. automethod:: set
    .. automethod:: update
    .. automethod:: clear
    .. automethod:: __getitem__
        
        Implements dict interface, allows to get cookie value by its name.

    .. automethod:: items
    .. automethod:: get_dict
    .. automethod:: load_from_file
    .. automethod:: save_to_file
