.. _tutorial:

=============
Grab Tutorial
=============

Usage of grab library consists of several repeatable steps:

 * Create grab instance and configure it (one time)
 * Build network request and submit it
 * Doing something with response

Grab uses pycurl to process HTTP requests and responses.
Grab have modular architecture - you can develop extension which will allow
to use grab with you favorite network library (urllib, urllib2, socket etc)

Live code examples
==================

Retreive google images search page and parse title tag contents::

    import re
    from grab import Grab

    g = Grab()
    g.go('http://images.google.com')
    print re.search('<title>([^>]+)</title>', g.response.body).group(1)

Also we can use XPath to process HTML. Under the hood Grab uses lxml library
to build HTML DOM Tree and search XPath expressions. Each lxml DOM element
provides ElementTree API. In following example we find element with XPath and
then use it text attribute which is provided by ElementTree API::

    print g.xpath('//title')[0].text

``xpath`` method is shortcut to ``g.tree.xpath`` where ``tree`` is the property
which returns lxml DOM tree. The DOM tree object is calculated only one time when
first call to ``tree`` attribute is occured. All subsequent call to ``tree`` attribute
retreive cached value. The ``g.xpath()`` is equivalent to ``g.tree.xpath`` which in turn
is equivalent to following code::

    from lxml.html import fromstring
    return fromstring(self.response.body)

Grab use many lxml features including form processing. Grab automatically parse HTML
forms and allow to submit them using their default values. You do not have to process 
hidden form fields - Grab will do it for you.

By defult Grab save cookies from response and submit them in subsequent requests. This allow
to emulate site sessions: sign in the site and fetch pages which requires user authorization.

In following example we log in bitbucket and send private message::

    from grab import Grab

    g = Grab(log_file='log.html')
    g.go('http://bitbucket.org/account/signin/')
    g.set_input('username', '...')
    g.set_input('password', '...')
    g.submit()

    g.go('/account/notifications/send/')
    g.set_input('recipient', 'lorien')
    g.set_input('title', 'Hi!')
    g.set_input('message', 'How are you?')
    g.submit()

``set_input`` sets the value of the input element in selected form. If you did not select the form
the Grab do it automatically. By default it selects the form with the most biggest
number of input elements.
