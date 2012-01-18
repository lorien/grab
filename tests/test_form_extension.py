# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
from util import (FakeServerThread, BASE_URL, RESPONSE, REQUEST,
                  ignore_transport)

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
           <input type="submit" value="submit2" class="submit_btn" name="submit" />
        </form>
    </div>
</body>
""".encode('utf-8')

POST_FORM = """
<form method="post" action="%s">
    <input type="text" name="secret" value="123"/>
    <input type="text" name="name" />
    <input type="text" disabled value="some_text" name="disabled_text" />
</form>
""" % BASE_URL

MULTIPLE_SUBMIT_FORM = """
<form method="post">
    <input type="text" name="secret" value="123"/>
    <input type="submit" name="submit1" value="submit1" />
    <input type="submit" name="submit2" value="submit2" />
</form>
"""

class TestHtmlForms(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.fake_response(FORMS)
        FakeServerThread().start()

    def test_choose_form(self):
        """
        Test ``choose_form`` method
        """
        
        # raise errors
        self.assertRaises(DataNotFound, lambda: self.g.choose_form(10))
        self.assertRaises(DataNotFound, lambda: self.g.choose_form(id='bad_id'))
        self.assertRaises(DataNotFound, lambda: self.g.choose_form(id='fake_form'))
        self.assertRaises(GrabMisuseError, lambda: self.g.choose_form())
        
        # check results
        self.g.choose_form(0)
        self.assertEqual('form', self.g._lxml_form.tag)
        self.assertEqual('search_form', self.g._lxml_form.get('id'))

        # reset current form
        self.g._lxml_form = None

        self.g.choose_form(id='common_form')
        self.assertEqual('form', self.g._lxml_form.tag)
        self.assertEqual('common_form', self.g._lxml_form.get('id'))

        # reset current form
        self.g._lxml_form = None

        self.g.choose_form(name='dummy')
        self.assertEqual('form', self.g._lxml_form.tag)
        self.assertEqual('dummy', self.g._lxml_form.get('name'))

        # reset current form
        self.g._lxml_form = None

        self.g.choose_form(xpath='//form[contains(@action, "/dummy")]')
        self.assertEqual('form', self.g._lxml_form.tag)
        self.assertEqual('dummy', self.g._lxml_form.get('name'))

    def test_submit(self):
        g = Grab()
        RESPONSE['get'] = POST_FORM
        g.go(BASE_URL)
        g.set_input('name', 'Alex')
        g.submit()
        self.assertEqual(REQUEST['post'], 'name=Alex&secret=123')

        # Default submit control
        RESPONSE['get'] = MULTIPLE_SUBMIT_FORM
        g.go(BASE_URL)
        g.submit()
        self.assertEqual(REQUEST['post'], 'secret=123&submit1=submit1')

        # Selected submit control
        RESPONSE['get'] = MULTIPLE_SUBMIT_FORM
        g.go(BASE_URL)
        g.submit(submit_name='submit2')
        self.assertEqual(REQUEST['post'], 'secret=123&submit2=submit2')

        # Default submit control if submit control name is invalid
        RESPONSE['get'] = MULTIPLE_SUBMIT_FORM
        g.go(BASE_URL)
        g.submit(submit_name='submit3')
        self.assertEqual(REQUEST['post'], 'secret=123&submit1=submit1')
