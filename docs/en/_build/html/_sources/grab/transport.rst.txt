.. _grab_transport:

Network Transport
=================

Grab can use two libraries to submit network requests: pycurl and urllib3. You may acess
transport object with `Grab.transport` attribute. In most cases you do not need direct
access to transport object.

Pycurl transport
----------------

The pycurl transport is the default network transport. You can control low-level options
of pycurl object by accessing `Grab.transport.pycurl` object. For example:

..  code:: python

    from grab import Grab
    import pycurl

    grab = Grab()
    grab.transport.pycurl.setopt(pycurl.LOW_SPEED_LIMIT, 100)
    grab.go('http://example.com/download/porn.mpeg')

Urllib3 transport
-----------------

If you want to use Grab in gevent environment then consider to use urllib3 transport.
The urllib3 uses native python sockets that could be patched by `gevent.monkey.patch_all`.

..  code:: python

    import gevent
    import gevent.monkey
    from grab import Grab
    import time


    def worker():
        g = Grab(user_agent='Medved', transport='urllib3')
        # Request the document that is served with 1 second delay
        g.go('http://httpbin.org/delay/1')
        return g.doc.json['headers']['User-Agent']


    started = time.time()
    gevent.monkey.patch_all()
    pool = []
    for _ in range(10):
        pool.append(gevent.spawn(worker))
    for th in pool:
        th.join()
        assert th.value == 'Medved'
    # The total time would be less than 2 seconds
    # unless you have VERY bad internet connection
    assert (time.time() - started) < 2

Use your own transport
----------------------

You can implement you own transport class and use it. Just pass
your transport class to `transport` option.

Here is the crazy example of wget-powered transport. Note that this is
VERY simple transport that understands only one option: the URL.

..  code:: python

    from grab import Grab
    from grab.document import Document
    from subprocess import check_output


    class WgetTransport(object):
        def __init__(self):
            self.request_head = b''
            self.request_body = b''

        def reset(self): pass

        def process_config(self, grab):
            self._request_url = grab.config['url']

        def request(self):
            out = check_output(['/usr/bin/wget', '-O', '-',
                                self._request_url])
            self._response_body = out

        def prepare_response(self, grab):
            doc = Document()
            doc.body = self._response_body
            return doc


    g = Grab(transport=WgetTransport)
    g.go('http://protonmail.com')
    assert 'Secure email' in g.doc('//title').text()
