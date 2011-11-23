.. _extensions_text:

Working with text content of response
=====================================

Each method of this extension could work with two kind of data:
with original byte-sting response and with response converted to unicode.
To avoid confusion you should manually specify with wich kind of data you
want to work. In short, be default all these methods expect unicode arguments,
so just use unicode.

Some examples::

    g = Grab()
    g.go('some url')

    # Check that response contains the string "moon"
    if grab.search(u'moon'):
        ...

    # And now check for moon in any letter-case
    if grab.search_rex(re.compile('moon', re.I)):
        ...

    # `search_rex` method returns regexp match object or None
    # We can use found match object
    match = grab.search_rex(re.compile('(\d+) days'))
    if match:
        print 'Number of days: %s' % match.group(1)

    # Check for moon and raise DataNotFound exception
    # if it does not exist in document
    grab.assert_substring(u'moon')

    # Raise exception if no moon AND no sun in document
    grab.assert_substrings((u'moon', u'sun'))

    # Raise exception if no numbers in document
    grab.assert_rex(re.compile('\d'))

Text Extension API
------------------

.. module:: grab.ext.text

.. autoclass:: TextExtension

    .. automethod:: search
    .. automethod:: search_rex
    .. automethod:: assert_substring
    .. automethod:: assert_substrings
    .. automethod:: assert_rex
