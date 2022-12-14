from mock import patch
from test_server import Response

from grab import Grab, base
from tests.util import BaseGrabTestCase, build_grab


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_debug_post(self):
        grab = build_grab(debug_post=True)
        grab.setup(post={"foo": "bar"})
        self.server.add_response(Response(data=b"x"))
        grab.go(self.server.get_url())
        self.assertEqual(b"x", grab.doc.body)

    def test_debug_nonascii_post(self):
        self.server.add_response(Response())
        grab = build_grab(debug=True)
        grab.setup(post="фыва".encode("cp1251"))
        grab.go(self.server.get_url())

    def test_debug_nonascii_multipart_post(self):
        self.server.add_response(Response())
        grab = build_grab(debug=True)
        grab.setup(charset="cp1251", multipart_post=[("x", "фыва".encode("cp1251"))])
        grab.go(self.server.get_url())

    def test_debug_post_integer_bug(self):
        grab = build_grab(debug_post=True)
        grab.setup(post={"foo": 3})
        self.server.add_response(Response(data=b"x"))
        grab.go(self.server.get_url())
        self.assertEqual(b"x", grab.doc.body)

    def test_debug_post_big_str(self):
        self.server.add_response(Response())
        grab = build_grab(debug_post=True)
        big_value = "x" * 1000
        grab.setup(post=big_value)
        grab.go(self.server.get_url())
        self.assertEqual(self.server.get_request().data, big_value.encode())

    def test_debug_post_dict_big_value(self):
        self.server.add_response(Response())
        grab = build_grab(debug_post=True)
        big_value = "x" * 1000
        grab.setup(
            post={
                "foo": big_value,
            }
        )
        grab.go(self.server.get_url())
        self.assertEqual(
            self.server.get_request().data, ("foo=%s" % big_value).encode()
        )

    def test_log_request_extra_argument(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.go(self.server.get_url())
        with patch.object(base.logger_network, "debug") as mocked:
            grab.log_request()
            args = mocked.mock_calls[0][1]
            self.assertEqual("", args[3])

        with patch.object(base.logger_network, "debug") as mocked:
            grab.log_request(extra="zz")
            args = mocked.mock_calls[0][1]
            self.assertEqual("[zz] ", args[3])

    def test_setup_document_logging(self):
        grab = Grab()
        grab.setup_document(b"abc")
        with patch.object(base.logger_network, "debug") as mocked:
            grab.log_request()
            args = mocked.mock_calls[0][1]
            # request_counter is 0 and formatted as "00"
            self.assertEqual("00", args[1])

    #    grab.log_request()  # should not raise exception
