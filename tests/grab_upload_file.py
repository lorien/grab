# coding: utf-8
import os

from grab import UploadContent, UploadFile
from tests.util import build_grab, temp_file, BaseGrabTestCase


class TestUploadContent(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def prepare_form_grab(self):
        url = self.server.get_url()
        html = (
            '<form action="%s" method="post" enctype="multipart/form-data">'
            '<input type="file" name="image">'
            '</form>' % url
        ).encode('ascii')
        grab = build_grab(html, charset='utf-8')
        return grab

    # *******************
    # UploadContent Tests
    # *******************

    def test_upload_content_filename(self):
        grab = self.prepare_form_grab()
        data = b'foo'
        upload_data = UploadContent(data, filename='avatar.jpg')
        grab.doc.set_input('image', upload_data)
        grab.doc.submit(make_request=False)
        post = dict(grab.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadContent))

        grab.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertEqual('avatar.jpg',
                         self.server.request['files']['image'][0]['filename'])
        self.assertEqual(
            'image/jpeg',
            self.server.request['files']['image'][0]['content_type'])

    def test_upload_content_random_filename(self):
        grab = self.prepare_form_grab()
        data = b'foo'
        upload_data = UploadContent(data)
        grab.doc.set_input('image', upload_data)
        grab.doc.submit(make_request=False)
        post = dict(grab.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadContent))

        grab.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertEqual(
            10, len(self.server.request['files']['image'][0]['filename']))
        self.assertEqual(
            'application/octet-stream',
            self.server.request['files']['image'][0]['content_type'])

    def test_upload_content_content_type(self):
        grab = self.prepare_form_grab()
        data = b'foo'
        upload_data = UploadContent(data,
                                    content_type='application/grab')
        grab.doc.set_input('image', upload_data)
        grab.doc.submit(make_request=False)
        post = dict(grab.config['multipart_post'])
        self.assertTrue(isinstance(post['image'], UploadContent))

        grab.doc.submit()
        self.assertEqual(data,
                         self.server.request['files']['image'][0]['body'])
        self.assertEqual(
            10, len(self.server.request['files']['image'][0]['filename']))
        self.assertEqual(
            'application/grab',
            self.server.request['files']['image'][0]['content_type'])

    # ****************
    # UploadFile Tests
    # ****************

    def test_upload_file(self):
        with temp_file() as file_path:
            grab = self.prepare_form_grab()
            data = b'foo'
            with open(file_path, 'wb') as out:
                out.write(data)
            upload_data = UploadFile(file_path)
            grab.doc.set_input('image', upload_data)
            grab.doc.submit(make_request=False)
            post = dict(grab.config['multipart_post'])
            self.assertTrue(isinstance(post['image'], UploadFile))

            grab.doc.submit()
            self.assertEqual(data,
                             self.server.request['files']['image'][0]['body'])
            _, filename = os.path.split(file_path)
            self.assertEqual(
                filename,
                self.server.request['files']['image'][0]['filename'],
            )
            self.assertEqual(
                'application/octet-stream',
                self.server.request['files']['image'][0]['content_type'])

    def test_upload_file_custom_filename(self):
        with temp_file() as file_path:
            grab = self.prepare_form_grab()
            data = b'foo'
            with open(file_path, 'wb') as out:
                out.write(data)
            upload_data = UploadFile(file_path, filename='avatar.jpg')
            grab.doc.set_input('image', upload_data)
            grab.doc.submit(make_request=False)
            post = dict(grab.config['multipart_post'])
            self.assertTrue(isinstance(post['image'], UploadFile))

            grab.doc.submit()
            self.assertEqual(data,
                             self.server.request['files']['image'][0]['body'])
            self.assertEqual(
                'avatar.jpg',
                self.server.request['files']['image'][0]['filename'],
            )
            self.assertEqual(
                'image/jpeg',
                self.server.request['files']['image'][0]['content_type'])

    def test_upload_file_custom_content_type(self):
        with temp_file() as file_path:
            grab = self.prepare_form_grab()
            data = b'foo'
            with open(file_path, 'wb') as out:
                out.write(data)
            upload_data = UploadFile(file_path, filename='avatar.jpg',
                                     content_type='application/grab')
            grab.doc.set_input('image', upload_data)
            grab.doc.submit(make_request=False)
            post = dict(grab.config['multipart_post'])
            self.assertTrue(isinstance(post['image'], UploadFile))

            grab.doc.submit()
            self.assertEqual(data,
                             self.server.request['files']['image'][0]['body'])
            self.assertEqual(
                'avatar.jpg',
                self.server.request['files']['image'][0]['filename'],
            )
            self.assertEqual(
                'application/grab',
                self.server.request['files']['image'][0]['content_type'])
