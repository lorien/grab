# import os
#
# from test_server import Response
#
# from grab import UploadContent, UploadFile
# from tests.util import BaseTestCase, temp_file
#
#
# class TestUploadContent(BaseTestCase):
#    def setUp(self) -> None:
#        self.server.reset()
#
#    def prepare_form_grab(self):
#        url = self.server.get_url()
#        self.server.add_response(
#            Response(
#                data=(
#                    '<form action="%s" method="post" enctype="multipart/form-data">'
#                    '<input type="file" name="image">'
#                    "</form>" % url
#                ).encode("ascii")
#            )
#        )
#        grab = Grab()
#        grab.request(self.server.get_url())
#        return grab
#
#    # *******************
#    # UploadContent Tests
#    # *******************
#
#    def test_upload_content_filename(self):
#       grab = self.prepare_form_grab()
#       self.server.add_response(Response(), count=2)
#       data = b"foo"
#       upload_data = UploadContent(data, filename="avatar.jpg")
#       grab.doc.set_input("image", upload_data)
#       grab.submit(make_request=False)
#       post = dict(grab.config["multipart_post"])
#       self.assertTrue(isinstance(post["image"], UploadContent))
#
#       grab.submit()
#       self.assertEqual(data, self.server.request.files["image"][0]["content"])
#       self.assertEqual(
#           "avatar.jpg", self.server.request.files["image"][0]["filename"]
#       )
#       self.assertEqual(
#           "image/jpeg", self.server.request.files["image"][0]["content_type"]
#       )
#
#    def test_upload_content_random_filename(self):
#       grab = self.prepare_form_grab()
#       self.server.add_response(Response(), count=2)
#       data = b"foo"
#       upload_data = UploadContent(data)
#       grab.doc.set_input("image", upload_data)
#       grab.submit(make_request=False)
#       post = dict(grab.config["multipart_post"])
#       self.assertTrue(isinstance(post["image"], UploadContent))
#
#       grab.submit()
#       self.assertEqual(data, self.server.request.files["image"][0]["content"])
#       self.assertEqual(10, len(self.server.request.files["image"][0]["filename"]))
#       self.assertEqual(
#           "application/octet-stream",
#           self.server.request.files["image"][0]["content_type"],
#       )
#
#    def test_upload_content_content_type(self):
#       grab = self.prepare_form_grab()
#       self.server.add_response(Response(), count=2)
#       data = b"foo"
#       upload_data = UploadContent(data, content_type="application/grab")
#       grab.doc.set_input("image", upload_data)
#       grab.submit(make_request=False)
#       post = dict(grab.config["multipart_post"])
#       self.assertTrue(isinstance(post["image"], UploadContent))
#
#       grab.submit()
#       self.assertEqual(data, self.server.request.files["image"][0]["content"])
#       self.assertEqual(10, len(self.server.request.files["image"][0]["filename"]))
#       self.assertEqual(
#           "application/grab", self.server.request.files["image"][0]["content_type"]
#       )
#
#     ****************
#     UploadFile Tests
#     ****************
#
#    def test_upload_file(self):
#       with temp_file() as file_path:
#           grab = self.prepare_form_grab()
#           self.server.add_response(Response(), count=2)
#           data = b"foo"
#           with open(file_path, "wb") as out:
#               out.write(data)
#           upload_data = UploadFile(file_path)
#           grab.doc.set_input("image", upload_data)
#           grab.submit(make_request=False)
#           post = dict(grab.config["multipart_post"])
#           self.assertTrue(isinstance(post["image"], UploadFile))
#
#           grab.submit()
#           self.assertEqual(data, self.server.request.files["image"][0]["content"])
#           _, filename = os.path.split(file_path)
#           self.assertEqual(
#               filename,
#               self.server.request.files["image"][0]["filename"],
#           )
#           self.assertEqual(
#               "application/octet-stream",
#               self.server.request.files["image"][0]["content_type"],
#           )
#
#    def test_upload_file_custom_filename(self):
#       with temp_file() as file_path:
#           grab = self.prepare_form_grab()
#           self.server.add_response(Response(), count=2)
#           data = b"foo"
#           with open(file_path, "wb") as out:
#               out.write(data)
#           upload_data = UploadFile(file_path, filename="avatar.jpg")
#           grab.doc.set_input("image", upload_data)
#           grab.submit(make_request=False)
#           post = dict(grab.config["multipart_post"])
#           self.assertTrue(isinstance(post["image"], UploadFile))
#
#           grab.submit()
#           self.assertEqual(data, self.server.request.files["image"][0]["content"])
#           self.assertEqual(
#               "avatar.jpg",
#               self.server.request.files["image"][0]["filename"],
#           )
#           self.assertEqual(
#               "image/jpeg", self.server.request.files["image"][0]["content_type"]
#           )
#
#    def test_upload_file_custom_content_type(self):
#       with temp_file() as file_path:
#           grab = self.prepare_form_grab()
#           self.server.add_response(Response(), count=2)
#           data = b"foo"
#           with open(file_path, "wb") as out:
#               out.write(data)
#           upload_data = UploadFile(
#               file_path, filename="avatar.jpg", content_type="application/grab"
#           )
#           grab.doc.set_input("image", upload_data)
#           grab.submit(make_request=False)
#           post = dict(grab.config["multipart_post"])
#           self.assertTrue(isinstance(post["image"], UploadFile))
#
#           grab.submit()
#           self.assertEqual(data, self.server.request.files["image"][0]["content"])
#           self.assertEqual(
#               "avatar.jpg",
#               self.server.request.files["image"][0]["filename"],
#           )
#           self.assertEqual(
#               "application/grab",
#               self.server.request.files["image"][0]["content_type"],
#           )
