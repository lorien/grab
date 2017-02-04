# coding: utf-8
"""
See details here: https://github.com/tiran/defusedxml/blob/master/README.md
"""
from test.util import temp_dir, build_grab
from test.util import BaseGrabTestCase
import os
from lxml.etree import parse
from six import BytesIO
from defusedxml import EntitiesForbidden


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_lxml_security_bug(self):
        with temp_dir() as tmp_dir:
            inj_file = os.path.join(tmp_dir, 'injection')
            with open(inj_file, 'w') as out:
                out.write('Hey there!')
            bad_xml = (
                '<!DOCTYPE external ['
                '<!ENTITY ee SYSTEM "file://' + inj_file + '">'
                ']>'
                '<root>&ee;</root>'
            ).encode()
            tree = parse(BytesIO(bad_xml))
            self.assertEqual(tree.xpath('//root/text()')[0], 'Hey there!')

    def test_grab_parse_defensedxml(self):
        with temp_dir() as tmp_dir:
            inj_file = os.path.join(tmp_dir, 'injection')
            xml_file = os.path.join(tmp_dir, 'bad.xml')
            with open(inj_file, 'w') as out:
                out.write('Hey there!')
            bad_xml = (
                '<!DOCTYPE external ['
                '<!ENTITY ee SYSTEM "file://' + inj_file + '">'
                ']>'
                '<root>&ee;</root>'
            ).encode()
            with open(xml_file, 'wb') as out:
                out.write(bad_xml)
            g = build_grab(content_type='xml')
            g.go('file://%s' % xml_file)
            self.assertRaises(EntitiesForbidden, g.doc, '//title')
