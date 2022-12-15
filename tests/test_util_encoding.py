import codecs
from unittest import TestCase

from grab.util.encoding import make_bytes, make_str, read_bom


class UtilEncodingMakeStrTestCase(TestCase):
    def test_make_str_nontext(self):
        self.assertEqual("{1: 2}", make_str({1: 2}))

    def test_make_str_str(self):
        self.assertEqual("foo", make_str("foo"))

    def test_make_str_bytes(self):
        self.assertEqual("foo", make_str(b"foo"))

    def test_make_str_bytes_encoding(self):
        self.assertEqual("луна", make_str("луна".encode("cp1251"), encoding="cp1251"))

    def test_make_str_bytes_wrong_encoding_ignore(self):
        self.assertEqual(
            "",
            make_str("луна".encode("cp1251"), encoding="utf-8", errors="ignore"),
        )


class UtilEncodingMakeBytesTestCase(TestCase):
    def test_make_str_nontext(self):
        self.assertEqual(b"{1: 2}", make_bytes({1: 2}))

    def test_make_bytes_str(self):
        self.assertEqual(b"foo", make_bytes("foo"))

    def test_make_bytes_bytes(self):
        self.assertEqual("луна".encode("utf-8"), make_bytes("луна"))

    def test_make_bytes_bytes_encoding(self):
        self.assertEqual("луна".encode("cp1251"), make_bytes("луна", encoding="cp1251"))

    def test_make_bytes_bytes_wrong_encoding_ignore(self):
        self.assertEqual(
            b"",
            make_bytes("луна", encoding="ascii", errors="ignore"),
        )


class BomTestCase(TestCase):
    """The BOM is Byte Order Mark in Unicode."""

    def test_empty_data(self):
        self.assertEqual(read_bom(b""), (None, None))

    def test_utf8_with_bom(self):
        self.assertEqual(
            read_bom(codecs.BOM_UTF8 + "сплин".encode("utf-8")),
            ("utf-8", codecs.BOM_UTF8),
        )

    def test_utf16le_with_bom(self):
        self.assertEqual(
            read_bom(codecs.BOM_UTF16_LE + "сплин".encode("utf-16-le")),
            ("utf-16-le", codecs.BOM_UTF16_LE),
        )
