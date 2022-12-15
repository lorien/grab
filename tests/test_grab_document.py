from test_server import Response

from grab.document import normalize_pairs
from grab.error import GrabFeatureIsDeprecated
from tests.util import BaseGrabTestCase, build_grab


class GrabDocumentTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_copy_works(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"<h1>test</h1>"))
        res1 = grab.go(self.server.get_url())
        self.assertEqual("test", res1.select("//h1").text())

        res2 = res1.copy()
        self.assertEqual("test", res2.select("//h1").text())

    def test_document_copy_with_other_grab_deprecated(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"<h1>test</h1>"))
        res1 = grab.go(self.server.get_url())

        grab2 = build_grab()
        with self.assertRaises(GrabFeatureIsDeprecated):
            res1.copy(grab2)

    # def test_document_copy_with_other_grab_config(self):
    #    grab = build_grab()
    #    self.server.add_response(Response(data=b"foo"))
    #    res1 = grab.go(self.server.get_url())

    #    grab2 = build_grab()
    #    self.server.add_response(Response(data=b"bar"))
    #    res2 = grab2.go(self.server.get_url())
    #    self.assertEqual(res2.body, b"bar")

    #    res3 = res1.copy(grab2.config)
    #    self.assertEqual(res3.body, b"bar")

    def test_normalize_pairs_dict(self):
        self.assertEqual(
            normalize_pairs({"foo": "bar"}),
            [("foo", "bar")],
        )

    def test_normalize_pairs_list(self):
        self.assertEqual(
            normalize_pairs([("foo", "bar"), ("1", "2")]),
            [("foo", "bar"), ("1", "2")],
        )
