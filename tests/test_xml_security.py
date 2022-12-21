# Reference:
# https://lxml.de/FAQ.html#how-do-i-use-lxml-safely-as-a-web-service-endpoint
import os
from io import BytesIO

from lxml.etree import parse

from tests.util import BaseGrabTestCase, temp_dir


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_lxml_security_bug(self):
        with temp_dir() as tmp_dir:
            injection_path = os.path.join(tmp_dir, "injection")
            with open(injection_path, "w", encoding="utf-8") as out:
                out.write("Hey there!")
            # Prepare file:// URL valid for both linux and windows
            injection_url = "file:///%s" % (
                injection_path.lstrip("/").replace("\\", "/")
            )
            bad_xml = (
                "<!DOCTYPE external ["
                '<!ENTITY ee SYSTEM "' + injection_url + '">'
                "]>"
                "<root>&ee;</root>"
            ).encode()
            tree = parse(BytesIO(bad_xml))
            self.assertEqual(tree.xpath("//root/text()")[0], "Hey there!")
