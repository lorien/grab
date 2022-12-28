# Reference:
# https://lxml.de/FAQ.html#how-do-i-use-lxml-safely-as-a-web-service-endpoint

import os
import typing
from io import BytesIO
from typing import cast

from lxml.etree import parse

from tests.util import BaseTestCase, temp_dir


class GrabSimpleTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_lxml_security_bug(self) -> None:
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
            # pylint: disable=deprecated-typing-alias
            self.assertEqual(
                cast(typing.List[str], tree.xpath("//root/text()"))[0],
                "Hey there!",
            )
