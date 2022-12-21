from copy import deepcopy

from test_server import Response

from grab import GrabError, GrabMisuseError
from grab.document import Document
from tests.util import BaseGrabTestCase, build_grab


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_incorrect_option_name(self):
        grab = build_grab()
        self.assertRaises(GrabMisuseError, grab.setup, save_the_word=True)

    def test_clone(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"Moon"))
        grab.request(self.server.get_url())
        self.assertTrue(b"Moon" in grab.doc.body)
        self.server.add_response(Response(data=b"Foo"))
        grab2 = grab.clone(method="post", post="")
        grab2.request(self.server.get_url())
        self.assertTrue(b"Foo" in grab2.doc.body)

    def test_empty_clone(self):
        grab = build_grab()
        grab.clone()

    def test_make_url_absolute(self):
        grab = build_grab()
        self.server.add_response(Response(data=b'<base href="http://foo/bar/">'))
        grab.request(self.server.get_url())
        absolute_url = grab.make_url_absolute("/foobar", resolve_base=True)
        self.assertEqual(absolute_url, "http://foo/foobar")
        grab = build_grab()
        absolute_url = grab.make_url_absolute("/foobar")
        self.assertEqual(absolute_url, "/foobar")

    def test_error_request(self):
        grab = build_grab()
        grab.setup(post={"foo": "bar"})

        self.assertRaises(GrabError, grab.request, url="Could-not-resolve-host-address")
        self.assertEqual(grab.config["post"], None)
        self.assertEqual(grab.config["multipart_post"], None)
        self.assertEqual(grab.config["method"], None)

    def test_document(self):
        data = b"""
        <h1>test</h1>
        """
        doc = Document(data)
        self.assertTrue(b"test" in doc.body)

    def test_document_invalid_input(self):
        data = """
        <h1>test</h1>
        """
        self.assertRaises(GrabMisuseError, Document, data)

    def test_headers_affects_common_headers(self):
        grab = build_grab()
        ch_origin = deepcopy(grab.config["common_headers"])
        # Provide custom header which is also in common_headers
        grab.setup(headers={"Accept": "zzz"})
        # To make request Grab processes config and build result headers
        # from `config['common_headers']` and `config['headers']
        # That merge should not change initial `config['common_headers']` value
        grab.request(self.server.get_url())
        self.assertEqual(
            grab.config["common_headers"]["Accept"],
            ch_origin["Accept"],
        )
