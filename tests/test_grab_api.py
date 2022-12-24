from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from grab import Grab
from grab.document import Document
from grab.errors import GrabMisuseError
from tests.util import BaseGrabTestCase


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_incorrect_option_name(self):
        with self.assertRaises(GrabMisuseError):
            Grab().setup(save_the_word=True)

    def test_clone(self):
        grab = Grab()
        self.server.add_response(Response(data=b"Moon"))
        doc = grab.request(self.server.get_url())
        self.assertTrue(b"Moon" in doc.body)

        self.server.add_response(Response(data=b"Foo"))
        grab2 = grab.clone()

        doc = grab2.request(self.server.get_url())
        self.assertTrue(b"Foo" in doc.body)

    def test_empty_clone(self):
        Grab().clone()

    # def test_make_url_absolute(self):
    #    self.server.add_response(Response(data=b'<base href="http://foo/bar/">'))
    #    request(self.server.get_url())
    #    absolute_url = grab.make_url_absolute("/foobar", resolve_base=True)
    #    self.assertEqual(absolute_url, "http://foo/foobar")
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
