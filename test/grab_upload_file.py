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

    def test_upload_file(self):
        url = self.server.get_url()
        html = ('''<form action="%s" method="post" enctype="multipart/form-data">
            <input type="file" name="image">
        </form>''' % url).encode('ascii')
        g = build_grab(html, charset='utf-8')

        fh, path = tempfile.mkstemp()
        data = b'foo'
        with open(path, 'wb') as out:
            out.write(data)
        upload_data = UploadFile(path)
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadFile))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])

    def test_upload_content(self):
        url = self.server.get_url()
        html = ('''<form action="%s" method="post" enctype="multipart/form-data">
            <input type="file" name="image">
        </form>''' % url).encode('ascii')
        g = build_grab(html, charset='utf-8')

        data = b'foo'
        upload_data = UploadContent(data, filename='avatar.jpg')
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadContent))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertEqual('avatar.jpg',
                         self.server.request['files']['image'][0]['filename'])

    def test_upload_content_random_filename(self):
        url = self.server.get_url()
        html = ('''<form action="%s" method="post" enctype="multipart/form-data">
            <input type="file" name="image">
        </form>''' % url).encode('ascii')
        g = build_grab(html, charset='utf-8')

        data = b'foo'
        upload_data = UploadContent(data)
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadContent))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertTrue(
            10, len(self.server.request['files']['image'][0]['filename']))
