from unittest import TestCase

from grab.util.encoding import make_bytes


class UtilEncodingMakeBytesTestCase(TestCase):
    def test_make_bytes_nontext(self):
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
