import codecs
from unittest import TestCase

from grab.util.charset import parse_bom


class BomTestCase(TestCase):
    """The BOM is Byte Order Mark in Unicode."""

    def test_empty_data(self):
        self.assertEqual(parse_bom(b""), (None, None))

    def test_utf8_with_bom(self):
        self.assertEqual(
            parse_bom(codecs.BOM_UTF8 + "сплин".encode("utf-8")),
            ("utf-8", codecs.BOM_UTF8),
        )

    def test_utf16le_with_bom(self):
        self.assertEqual(
            parse_bom(codecs.BOM_UTF16_LE + "сплин".encode("utf-16-le")),
            ("utf-16-le", codecs.BOM_UTF16_LE),
        )
