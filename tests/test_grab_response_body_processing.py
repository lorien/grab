import os

from test_server import Response

from grab import GrabMisuseError
from grab.base import Grab
from grab.document import Document
from tests.util import (
    TEST_DIR,
    BaseGrabTestCase,
    build_grab,
    build_grab_custom_subclass,
)


class CustomDocument(Document):
    def get_bytes_body(self):
        return self._bytes_body


class CustomGrab(Grab):
    document_class = CustomDocument


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_body_get_bytes_body_true(self):
        grab = build_grab_custom_subclass(CustomGrab)
        self.server.add_response(Response(data=b"bar"))
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.get_bytes_body(), b"bar")

    def test_access_null_body(self):
        grab = build_grab()
        self.assertEqual(grab.doc, None)

    def test_external_set_document_body(self):
        grab = build_grab()
        grab.go(self.server.get_url())
        with self.assertRaises(GrabMisuseError):
            grab.doc.body = b"asdf"

    def test_empty_response(self):
        self.server.add_response(Response(data=b""))
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(grab.doc.tree is not None)  # should not raise exception

    def test_doc_tree_notags_document(self):
        data = b"test"
        grab = build_grab(data)
        self.assertEqual(grab.doc.select("//html").text(), "test")

    def test_github_html_processing(self):
        # This test is for osx and py3.5
        # See: https://github.com/lorien/grab/issues/199

        # It should works with recent lxml builds on any platform.
        # In the past it failed on previous lxml releases on macos platform
        path = os.path.join(TEST_DIR, "files/github_showcases.html")
        with open(path, "rb") as inp:
            data = inp.read()
        self.server.add_response(Response(data=data))
        grab = build_grab()
        grab.go(self.server.get_url())
        items = []
        for elem in grab.doc.select('//a[contains(@class, "exploregrid-item")]'):
            items.append(grab.make_url_absolute(elem.attr("href")))
        self.assertTrue("tools-for-open-source" in items[2])

    def test_explicit_custom_charset(self):
        grab = build_grab(
            "<html><head></head><body><h1>привет</h1></body></html".encode("cp1251"),
            document_charset="cp1251",
        )
        self.assertEqual("привет", grab.doc.select("//h1").text())

    def test_json(self):
        self.server.add_response(Response(data=b'{"foo": "bar"}'))
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual({"foo": "bar"}, grab.doc.json)
