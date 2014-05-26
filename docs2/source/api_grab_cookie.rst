.. _api_grab_cookie:

.. module:: grab.cookie

Module grab.cookie
==================

This modules contains some classes to operate cookies.

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

    .. _grab_cookies_load_from_file:

    .. automethod:: load_from_file

    .. _grab_cookies_save_to_file:

    .. automethod:: save_to_file
