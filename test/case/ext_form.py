# coding: utf-8
from unittest import TestCase
try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from grab import Grab, DataNotFound, GrabMisuseError
from test.util import ignore_transport, build_grab
from test.server import SERVER

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
          <input type="text" id="some_value" name="some_value" value="" />
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
""" % SERVER.BASE_URL

MULTIPLE_SUBMIT_FORM = """
<form method="post">
    <input type="text" name="secret" value="123"/>
    <input type="submit" name="submit1" value="submit1" />
    <input type="submit" name="submit2" value="submit2" />
</form>
"""

NO_FORM_HTML = """
<div>Hello world</div>
"""

DISABLED_RADIO_HTML = """
<form>
    <input type="radio" name="foo" value="1" disabled="disabled" />
    <input type="radio" name="foo" value="2" disabled="disabled" />

    <input type="radio" name="bar" value="1" checked="checked" />
    <input type="radio" name="bar" value="2" disabled="disabled" />
</form>
"""

class TestHtmlForms(TestCase):
    def setUp(self):
        SERVER.reset()

        # Create fake grab instance with fake response
        self.g = build_grab()
        self.g.fake_response(FORMS)

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

    def assertEqualQueryString(self, qs1, qs2):
        args1 = set([(x, y[0]) for x, y in parse_qsl(qs1)])
        args2 = set([(x, y[0]) for x, y in parse_qsl(qs2)])
        self.assertEqual(args1, args2)

    def test_submit(self):
        g = build_grab()
        SERVER.RESPONSE['get'] = POST_FORM
        g.go(SERVER.BASE_URL)
        g.set_input('name', 'Alex')
        g.submit()
        self.assertEqualQueryString(SERVER.REQUEST['post'], 'name=Alex&secret=123')

        # Default submit control
        SERVER.RESPONSE['get'] = MULTIPLE_SUBMIT_FORM
        g.go(SERVER.BASE_URL)
        g.submit()
        self.assertEqualQueryString(SERVER.REQUEST['post'], 'secret=123&submit1=submit1')

        # Selected submit control
        SERVER.RESPONSE['get'] = MULTIPLE_SUBMIT_FORM
        g.go(SERVER.BASE_URL)
        g.submit(submit_name='submit2')
        self.assertEqualQueryString(SERVER.REQUEST['post'], 'secret=123&submit2=submit2')

        # Default submit control if submit control name is invalid
        SERVER.RESPONSE['get'] = MULTIPLE_SUBMIT_FORM
        g.go(SERVER.BASE_URL)
        g.submit(submit_name='submit3')
        self.assertEqualQueryString(SERVER.REQUEST['post'], 'secret=123&submit1=submit1')

    def test_set_methods(self):
        g = build_grab()
        SERVER.RESPONSE['get'] = FORMS
        g.go(SERVER.BASE_URL)

        self.assertEqual(g._lxml_form, None)

        g.set_input('gender', '1')
        self.assertEqual('common_form', g._lxml_form.get('id'))

        self.assertRaises(KeyError, lambda: g.set_input('query', 'asdf'))

        g._lxml_form = None
        g.set_input_by_id('search_box', 'asdf')
        self.assertEqual('search_form', g._lxml_form.get('id'))

        g.choose_form(xpath='//form[@id="common_form"]')
        g.set_input_by_number(0, 'asdf')

        g._lxml_form = None
        g.set_input_by_xpath('//*[@name="gender"]', '2')
        self.assertEqual('common_form', g._lxml_form.get('id'))

    def test_html_without_forms(self):
        g = build_grab()
        SERVER.RESPONSE['get'] = NO_FORM_HTML
        g.go(SERVER.BASE_URL)
        self.assertRaises(DataNotFound, lambda: g.form)

    def test_disabled_radio(self):
        """
        Bug #57
        """

        g = build_grab()
        SERVER.RESPONSE['get'] = DISABLED_RADIO_HTML
        g.go(SERVER.BASE_URL)
        g.submit(make_request=False)
