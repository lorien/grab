.. _grab_transport:

Network Transport
=================

Network transport is a component which utilize one of well known 3rd-party network packages
to do network requests and retrieve network response.  At the moment Grab supports only one
network library: urllib3. You may access transport object with `Grab.transport` attribute.
In most cases you do not need direct access to transport object.

Urllib3 transport
-----------------

This transport also could be used in gevent environment.
The urllib3 uses native python sockets that could be patched by `gevent.monkey.patch_all`.

..  code:: python

    import gevent
    import gevent.monkey
    from grab import Grab
    import time


    def worker():
        g = Grab(transport='urllib3')
        # Request the document that is served with 1 second delay
        g.request('http://httpbin.org/delay/1')
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

Here is minimal example to build Grab transport powered by wget.

..  code:: python

    import email.message
    from contextlib import contextmanager
    from subprocess import check_output

    from grab import Grab
    from grab.base_transport import BaseTransport
    from grab.document import Document


    class WgetTransport(BaseTransport):
        def reset(self):
            pass

        def process_config(self, grab_config, cookies):
            self._request_url = grab_config["url"]

        def request(self):
            out = check_output(["/usr/bin/wget", "-O", "-", self._request_url])
            self._response_body = out

        def prepare_response(self, grab_config, *, document_class=Document):
            return document_class(
                grab_config=grab_config,
                body=self._response_body,
                headers=email.message.Message(),
            )

        @contextmanager
        def wrap_transport_error(self):
            yield


    g = Grab(transport=WgetTransport)
    g.request("https://github.com")
    print(g.doc("//title").text())
    assert "github" in g.doc("//title").text().lower()

