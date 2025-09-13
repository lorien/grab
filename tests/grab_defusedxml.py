# coding: utf-8
"""
See details here: https://github.com/tiran/defusedxml/blob/master/README.md
"""
import os

from defusedxml import EntitiesForbidden
from lxml.etree import parse
from six import BytesIO

from tests.util import BaseGrabTestCase, build_grab, exclude_grab_transport, temp_dir


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    # def test_lxml_security_bug(self):
    #    with temp_dir() as tmp_dir:
    #        injection_path = os.path.join(tmp_dir, "injection")
    #        with open(injection_path, "w") as out:
    #            out.write("Hey there!")
    #        # Prepare file:// URL valid for both linux and windows
    #        injection_url = "file:///{}".format(
    #            injection_path.lstrip("/").replace("\\", "/")
    #        )
    #        bad_xml = (
    #            "<!DOCTYPE external ["
    #            '<!ENTITY ee SYSTEM "' + injection_url + '">'
    #            "]>"
    #            "<root>&ee;</root>"
    #        ).encode()
    #        tree = parse(BytesIO(bad_xml))
    #        self.assertEqual(tree.xpath("//root/text()")[0], "Hey there!")

    # @exclude_grab_transport("urllib3")
    # def test_grab_parse_defensedxml(self):
    #    with temp_dir() as tmp_dir:
    #        injection_path = os.path.join(tmp_dir, "injection")
    #        with open(injection_path, "w") as out:
    #            out.write("Hey there!")
    #        # Prepare file:// URL valid for both linux and windows
    #        injection_url = "file:///%s".format(
    #            injection_path.lstrip("/").replace("\\", "/")
    #        )
    #        bad_xml = (
    #            "<!DOCTYPE external ["
    #            '<!ENTITY ee SYSTEM "' + injection_url + '">'
    #            "]>"
    #            "<root>&ee;</root>"
    #        ).encode()
    #        xml_file = os.path.join(tmp_dir, "bad.xml")
    #        # On windows, use slashed instead of backslashes to avoid error:
    #        # Invalid file://hostname/, expected localhost or 127.0.0.1 or none
    #        if "\\" in xml_file:
    #            xml_file = xml_file.replace("\\", "/")
    #        with open(xml_file, "wb") as out:
    #            out.write(bad_xml)
    #        grab = build_grab(content_type="xml")
    #        file_url = "file://%s" % xml_file
    #        grab.go(file_url)
    #        self.assertRaises(EntitiesForbidden, grab.doc, "//title")
