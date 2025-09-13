# coding: utf-8
from copy import deepcopy

import six

from grab import GrabError, GrabMisuseError
from test_server import Request, Response
from tests.util import BaseGrabTestCase, build_grab, reset_request_counter, temp_file


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_incorrect_option_name(self):
        grab = build_grab()
        self.assertRaises(GrabMisuseError, grab.setup, save_the_word=True)

    def test_clone(self):
        grab = build_grab()
        self.server.add_response(Response(data="Moon"), count=1, method="get")
        grab.go(self.server.get_url())
        self.assertTrue(b"Moon" in grab.doc.body)
        self.server.add_response(Response(data="Foo"), method="post")
        grab2 = grab.clone(method="post", post="")
        grab2.go(self.server.get_url())
        self.assertTrue(b"Foo" in grab2.doc.body)

    def test_empty_clone(self):
        grab = build_grab()
        grab.clone()

    def test_adopt(self):
        grab = build_grab()
        self.server.add_response(Response(data="Moon"), count=1, method="get")
        grab.go(self.server.get_url())
        grab2 = build_grab()
        self.assertEqual(grab2.config["url"], None)
        grab2.adopt(grab)
        self.assertTrue(b"Moon" in grab2.doc.body)
        self.assertEqual(grab2.config["url"], self.server.get_url())

    def test_empty_adopt(self):
        grab = build_grab()
        grab2 = build_grab()
        grab2.adopt(grab)

    def test_default_content_for_fake_response(self):
        content = b"<strong>test</strong>"
        grab = build_grab(document_body=content)
        self.assertEqual(grab.doc.body, content)

    def test_inheritance(self):
        from grab import Grab

        class SimpleExtension(object):
            data = {"counter": 0}

            @classmethod
            def get_data(cls):
                return cls.data

        class CustomGrab(Grab, SimpleExtension):
            pass

        SimpleExtension.get_data()["counter"] = 0
        CustomGrab()
        # self.assertEqual(SimpleExtension.get_data()['counter'], 1)

        class VeryCustomGrab(CustomGrab):
            pass

        SimpleExtension.get_data()["counter"] = 0
        VeryCustomGrab()
        # self.assertEqual(SimpleExtension.get_data()['counter'], 1)

    def test_request_counter(self):
        import threading

        reset_request_counter()
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(grab.request_counter, 1)

        grab.go(self.server.get_url())
        self.assertEqual(grab.request_counter, 2)

        def func():
            grab = build_grab()
            grab.go(self.server.get_url())

        # Make 10 requests in concurrent threads
        threads = []
        for _ in six.moves.range(10):
            thread = threading.Thread(target=func)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

        grab.go(self.server.get_url())
        self.assertEqual(grab.request_counter, 13)

    def test_download(self):
        with temp_file() as save_file:
            grab = build_grab()
            self.server.add_response(Response(data="FOO"), count=1, method="get")
            length = grab.download(self.server.get_url(), save_file)
            self.assertEqual(3, length)

    def test_make_url_absolute(self):
        grab = build_grab()
        self.server.add_response(
            Response(data='<base href="http://foo/bar/">'), count=1, method="get"
        )
        grab.go(self.server.get_url())
        absolute_url = grab.make_url_absolute("/foobar", resolve_base=True)
        self.assertEqual(absolute_url, "http://foo/foobar")
        grab = build_grab()
        absolute_url = grab.make_url_absolute("/foobar")
        self.assertEqual(absolute_url, "/foobar")

    def test_error_request(self):
        grab = build_grab()
        grab.setup(post={"foo": "bar"})

        self.assertRaises(GrabError, grab.go, url="Could-not-resolve-host-address")
        self.assertEqual(grab.config["post"], None)
        self.assertEqual(grab.config["multipart_post"], None)
        self.assertEqual(grab.config["method"], None)
        self.assertEqual(grab.config["body_storage_filename"], None)

    def test_setup_document(self):
        data = b"""
        <h1>test</h1>
        """
        grab = build_grab(data)
        self.assertTrue(b"test" in grab.doc.body)

    # I have no idea why the document is invalid
    # def test_setup_document_invalid_input(self):
    #    data = """
    #    <h1>test</h1>
    #    """
    #    with self.assertRaises(GrabMisuseError):
    #        build_grab(data)

    def test_headers_affects_common_headers(self):
        grab = build_grab()
        ch_origin = deepcopy(grab.config["common_headers"])
        # Provide custom header which is also in common_headers
        grab.setup(headers={"Accept": "zzz"})
        # To make request Grab processes config and build result headers
        # from `config['common_headers']` and `config['headers']
        # That merge should not change initial `config['common_headers']` value
        grab.go(self.server.get_url())
        self.assertEqual(
            grab.config["common_headers"]["Accept"],
            ch_origin["Accept"],
        )
