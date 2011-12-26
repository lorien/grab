.. _extensions_lxml:

Extracting information from response with XPATH and CSS queries
===============================================================

Actually, all these methods are just a wrapers to `xpath` and `cssselect`
methods of `lxml.etree.Element` nodes.


LXML Extension API
------------------

.. module:: grab.ext.lxml

.. autoclass:: LXMLExtension

    .. autoattribute:: tree
    .. automethod:: find_link
    .. automethod:: find_link_rex
    .. automethod:: xpath
    .. automethod:: xpath_list
    .. automethod:: xpath_text
    .. automethod:: xpath_number
    .. automethod:: css
    .. automethod:: css_list
    .. automethod:: css_text
    .. automethod:: css_number
    .. automethod:: strip_tags
    .. automethod:: assert_css
    .. automethod:: strip_tags
    .. automethod:: css_exists
    .. automethod:: xpath_exists
    .. automethod:: find_content_blocks
