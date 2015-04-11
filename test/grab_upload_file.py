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

    def prepare_form_grab(self):
        url = self.server.get_url()
        html = ('''<form action="%s" method="post" enctype="multipart/form-data">
            <input type="file" name="image">
        </form>''' % url).encode('ascii')
        g = build_grab(html, charset='utf-8')
        return g

    # *******************
    # UploadContent Tests
    # *******************

    def test_upload_content_filename(self):
        g = self.prepare_form_grab()
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
        self.assertEqual(
            'image/jpeg',
            self.server.request['files']['image'][0]['content_type'])

    def test_upload_content_random_filename(self):
        g = self.prepare_form_grab()
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
        self.assertEqual(
            'application/octet-stream',
            self.server.request['files']['image'][0]['content_type'])

    def test_upload_content_content_type(self):
        g = self.prepare_form_grab()
        data = b'foo'
        upload_data = UploadContent(data,
                                    content_type='application/grab')
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadContent))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertTrue(
            10, len(self.server.request['files']['image'][0]['filename']))
        self.assertEqual(
            'application/grab',
            self.server.request['files']['image'][0]['content_type'])

    # ****************
    # UploadFile Tests
    # ****************

    def test_upload_file(self):
        g = self.prepare_form_grab()
        fh, file_path = tempfile.mkstemp()
        data = b'foo'
        with open(file_path, 'wb') as out:
            out.write(data)
        upload_data = UploadFile(file_path)
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadFile))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        filename = os.path.split(file_path)[1]
        self.assertEqual(filename,
                         self.server.request['files']['image'][0]['filename'])
        self.assertEqual(
            'application/octet-stream',
            self.server.request['files']['image'][0]['content_type'])

    def test_upload_file_custom_filename(self):
        g = self.prepare_form_grab()
        fh, file_path = tempfile.mkstemp()
        data = b'foo'
        with open(file_path, 'wb') as out:
            out.write(data)
        upload_data = UploadFile(file_path, filename='avatar.jpg')
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadFile))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertEqual('avatar.jpg',
                         self.server.request['files']['image'][0]['filename'])
        self.assertEqual(
            'image/jpeg',
            self.server.request['files']['image'][0]['content_type'])

    def test_upload_file_custom_content_type(self):
        g = self.prepare_form_grab()
        fh, file_path = tempfile.mkstemp()
        data = b'foo'
        with open(file_path, 'wb') as out:
            out.write(data)
        upload_data = UploadFile(file_path, filename='avatar.jpg',
                                 content_type='application/grab')
        g.doc.set_input('image', upload_data)
        g.doc.submit(make_request=False)
        post = dict(g.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadFile))

        g.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertEqual('avatar.jpg',
                         self.server.request['files']['image'][0]['filename'])
        self.assertEqual(
            'application/grab',
            self.server.request['files']['image'][0]['content_type'])
