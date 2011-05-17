.. _examples:

===================
Real World Examples
===================

Go to google, search for "grab pycurl" and display first ten results::

    g = Grab()
    g.go('http://www.google.ru')
    g.set_input('q', 'grab pycurl')
    g.submit()
    for elem in g.itercss('#rso li h3 a'):
        print u'%s | %s' % (elem.get('href'), elem.text_content().strip())

