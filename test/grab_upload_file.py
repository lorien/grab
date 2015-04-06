# coding: utf-8
from grab import UploadContent, UploadFile
import tempfile
import os
import pycurl
from test.util import build_grab
from test.util import BaseGrabTestCase

FORMS = u"""
<head>
    <title>Title</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
    <div id="header">
        <form id="search_form" method="GET">
            <input id="search_box" name="query" value="" />
            <input type="submit" value="submit" class="submit_btn"
                name="submit" />
        </form>
    </div>
    <div id="content">
        <FORM id="common_form" method="POST">
          <input id="some_value" name="some_value" value="" />
          <input id="some_value" name="image" type="file" value="" />
          <select id="gender" name="gender">
              <option value="1">Female</option>
              <option value="2">Male</option>
           </select>
           <input type="submit" value="submit" class="submit_btn"
            name="submit" />
        </FORM>
        <h1 id="fake_form">Big header</h1>
        <form name="dummy" action="/dummy">
           <input type="submit" value="submit" class="submit_btn"
           name="submit" />
        </form>
    </div>
</body>
""".encode('utf-8')


class TestUploadContent(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()
        # Create fake grab instance with fake response
        self.g = build_grab()
        self.g.setup_document(FORMS, charset='utf-8')

    def test(self):
        fc = UploadContent('a')
        self.assertEqual(fc, 'xxx')
        self.assertEqual(fc.field_tuple(), (pycurl.FORM_CONTENTS, 'a'))
        self.g.doc.set_input('image', fc)

        fc, path = tempfile.mkstemp()
        data = b'foo'
        with open(path, 'wb') as out:
            out.write(data)
        fc = UploadFile(path)
        self.assertEqual(fc, 'xxx')
        self.g.doc.set_input('image', fc)
        self.assertEqual(fc.field_tuple(), (pycurl.FORM_FILE, path))
        os.unlink(path)
