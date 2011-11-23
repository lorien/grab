# coding: utf-8
from unittest import TestCase

from grab import Grab, UploadContent

FORMS = u"""
<head>
    <title>Title</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
    <div id="header">
        <form id="search_form" method="GET">
            <input id="search_box" name="query" value="" />
            <input type="submit" value="submit" class="submit_btn" name="submit" />
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
           <input type="submit" value="submit" class="submit_btn" name="submit" />
        </FORM>
        <h1 id="fake_form">Big header</h1>
        <form name="dummy" action="/dummy">
           <input type="submit" value="submit" class="submit_btn" name="submit" />
        </form>
    </div>
</body>
""".encode('utf-8')

class TestUploadContent(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.fake_response(FORMS, charset='utf-8')

    def test(self):
        fc = UploadContent('a')
        self.assertEqual(fc, 'xxx')
        self.g.set_input('image', fc)
