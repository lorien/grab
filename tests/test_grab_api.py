from copy import deepcopy
from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from grab.document import Document
from grab.errors import GrabMisuseError
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
        doc = grab.request(self.server.get_url())
        self.assertTrue(b"Moon" in doc.body)

        self.server.add_response(Response(data=b"Foo"))
        grab2 = grab.clone()

        doc = grab2.request(self.server.get_url())
        self.assertTrue(b"Foo" in doc.body)

    def test_empty_clone(self):
        grab = build_grab()
        grab.clone()

    # def test_make_url_absolute(self):
    #    grab = build_grab()
    #    self.server.add_response(Response(data=b'<base href="http://foo/bar/">'))
    #    grab.request(self.server.get_url())
    #    absolute_url = grab.make_url_absolute("/foobar", resolve_base=True)
    #    self.assertEqual(absolute_url, "http://foo/foobar")
    #    grab = build_grab()
    #    absolute_url = grab.make_url_absolute("/foobar")
    #    self.assertEqual(absolute_url, "/foobar")

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
        # To make request Grab processes config and build result headers
        # from `config['common_headers']` and `config['headers']
        # That merge should not change initial `config['common_headers']` value
        # Provide custom header which is also in common_headers
        grab.request(self.server.get_url(), headers={"Accept": "zzz"})
        self.assertEqual(
            grab.config["common_headers"]["Accept"],
            ch_origin["Accept"],
        )
