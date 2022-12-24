import os.path

from test_server import Response

from grab import request
from tests.util import TEST_DIR, BaseGrabTestCase, temp_dir

HTML = """
Hello world
"""

IMG_FILE = os.path.join(TEST_DIR, "files", "yandex.png")


class TestResponse(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_save(self):
        """Test `Response.save` method."""
        with temp_dir() as tmp_dir:
            with open(IMG_FILE, "rb") as inp:
                img_data = inp.read()
            tmp_file = os.path.join(tmp_dir, "file.bin")
            self.server.add_response(Response(data=img_data))

            doc = request(self.server.get_url())
            doc.save(tmp_file)
            with open(tmp_file, "rb") as inp:
                self.assertEqual(inp.read(), img_data)

    def test_custom_charset(self):
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

    def test_xml_declaration(self):
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
