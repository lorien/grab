import os.path

from test_server import Response

from grab import request
from tests.util import BaseTestCase, temp_dir

HTML = """
Hello world
"""


class TestResponse(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_save(self) -> None:
        """Test `Response.save` method."""
        with temp_dir() as tmp_dir:
            img_data = b"zzzzzzzzzzzzzzzzz"
            tmp_file = os.path.join(tmp_dir, "file.bin")
            self.server.add_response(Response(data=img_data))

            doc = request(self.server.get_url())
            doc.save(tmp_file)
            with open(tmp_file, "rb") as inp:
                self.assertEqual(inp.read(), img_data)

    def test_custom_charset(self) -> None:
        self.server.add_response(
            Response(
                data=(
                    "<html><head><meta "
                    'http-equiv="Content-Type" content="text/html; '
                    'charset=utf8;charset=cp1251" /></head><body>'
                    "<h1>крокодил</h1></body></html>"
                ).encode("utf-8")
            )
        )
        doc = request(self.server.get_url())
        self.assertTrue("крокодил" in doc.unicode_body())

    def test_xml_declaration(self) -> None:
        # unicode_body() should return HTML with xml declaration (if it
        # exists in original HTML)
        self.server.add_response(
            Response(
                data=(
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    "<html><body><h1>тест</h1></body></html>"
                ).encode("utf-8")
            )
        )
        doc = request(self.server.get_url())
        ubody = doc.unicode_body()
        self.assertTrue("тест" in ubody)
        self.assertTrue("<?xml" in ubody)
