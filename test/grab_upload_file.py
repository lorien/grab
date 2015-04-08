# coding: utf-8
from grab import UploadContent, UploadFile
import tempfile
import os
import pycurl
from test.util import build_grab
from test.util import BaseGrabTestCase



class TestUploadContent(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test(self):
        html = '''<form method="post" enctype="multipart/form-data">
            <input type="file" name="image">
        </form>'''
        g = build_grab(html, charset='utf-8')

        fc = UploadContent('a')
        self.assertEqual(fc, 'xxx')
        self.assertEqual(fc.field_tuple(), (pycurl.FORM_CONTENTS, 'a'))
        g.doc.set_input('image', fc)

        fc, path = tempfile.mkstemp()
        data = b'foo'
        with open(path, 'wb') as out:
            out.write(data)
        fc = UploadFile(path)
        self.assertEqual(fc, 'xxx')
        g.doc.set_input('image', fc)
        self.assertEqual(fc.field_tuple(), (pycurl.FORM_FILE, path))
        os.unlink(path)
