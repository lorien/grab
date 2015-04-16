# coding: utf-8
try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from grab import DataNotFound, GrabMisuseError
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
          <input type="text" id="some_value" name="some_value" value="" />
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
           <input type="submit" value="submit2" class="submit_btn"
            name="submit" />
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
"""

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


class TestHtmlForms(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

        # Create fake grab instance with fake response
        self.g = build_grab()
        self.g.fake_response(FORMS)

    def test_choose_form(self):
        """
        Test ``choose_form`` method
        """

        # raise errors
        self.assertRaises(DataNotFound, self.g.choose_form, 10)
        self.assertRaises(DataNotFound, self.g.choose_form, id='bad_id')
        self.assertRaises(DataNotFound, self.g.choose_form, id='fake_form')
        self.assertRaises(GrabMisuseError, self.g.choose_form)

        # check results
        self.g.choose_form(0)
        self.assertEqual('form', self.g.doc._lxml_form.tag)
        self.assertEqual('search_form', self.g.doc._lxml_form.get('id'))

        # reset current form
        self.g.doc._lxml_form = None

        self.g.choose_form(id='common_form')
        self.assertEqual('form', self.g.doc._lxml_form.tag)
        self.assertEqual('common_form', self.g.doc._lxml_form.get('id'))

        # reset current form
        self.g.doc._lxml_form = None

        self.g.choose_form(name='dummy')
        self.assertEqual('form', self.g.doc._lxml_form.tag)
        self.assertEqual('dummy', self.g.doc._lxml_form.get('name'))

        # reset current form
        self.g.doc._lxml_form = None

        self.g.choose_form(xpath='//form[contains(@action, "/dummy")]')
        self.assertEqual('form', self.g.doc._lxml_form.tag)
        self.assertEqual('dummy', self.g.doc._lxml_form.get('name'))

    def assertEqualQueryString(self, qs1, qs2):
        args1 = set([(x, y) for x, y in parse_qsl(qs1)])
        args2 = set([(x, y) for x, y in parse_qsl(qs2)])
        self.assertEqual(args1, args2)

    def test_submit(self):
        g = build_grab()
        self.server.response['get.data'] = POST_FORM % self.server.get_url()
        g.go(self.server.get_url())
        g.set_input('name', 'Alex')
        g.submit()
        self.assertEqualQueryString(self.server.request['data'],
                                    b'name=Alex&secret=123')

        # Default submit control
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM
        g.go(self.server.get_url())
        g.submit()
        self.assertEqualQueryString(self.server.request['data'],
                                    b'secret=123&submit1=submit1')

        # Selected submit control
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM
        g.go(self.server.get_url())
        g.submit(submit_name='submit2')
        self.assertEqualQueryString(self.server.request['data'],
                                    b'secret=123&submit2=submit2')

        # Default submit control if submit control name is invalid
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM
        g.go(self.server.get_url())
        g.submit(submit_name='submit3')
        self.assertEqualQueryString(self.server.request['data'],
                                    b'secret=123&submit1=submit1')

    def test_set_methods(self):
        g = build_grab()
        self.server.response['get.data'] = FORMS
        g.go(self.server.get_url())

        self.assertEqual(g.doc._lxml_form, None)

        g.set_input('gender', '1')
        self.assertEqual('common_form', g.doc._lxml_form.get('id'))

        self.assertRaises(KeyError, lambda: g.set_input('query', 'asdf'))

        g.doc._lxml_form = None
        g.set_input_by_id('search_box', 'asdf')
        self.assertEqual('search_form', g.doc._lxml_form.get('id'))

        g.choose_form(xpath='//form[@id="common_form"]')
        g.set_input_by_number(0, 'asdf')

        g.doc._lxml_form = None
        g.set_input_by_xpath('//*[@name="gender"]', '2')
        self.assertEqual('common_form', g.doc._lxml_form.get('id'))

    def test_html_without_forms(self):
        g = build_grab()
        self.server.response['get.data'] = NO_FORM_HTML
        g.go(self.server.get_url())
        self.assertRaises(DataNotFound, lambda: g.form)

    def test_disabled_radio(self):
        """
        Bug #57
        """

        g = build_grab()
        self.server.response['get.data'] = DISABLED_RADIO_HTML
        g.go(self.server.get_url())
        g.submit(make_request=False)

    def test_set_input_by_xpath_regex(self):
        html = b'''
            <div><form action="" method="post"><input name="foo" type="text">
            <input name="bar" id="bar" type="text">
        '''
        g = build_grab(html)
        g.set_input_by_xpath('//input[re:test(@id, "^ba")]', 'bar-value')
        g.submit(make_request=False)
        self.assertEqual(
            set([('foo', None), ('bar', 'bar-value')]),
            set(g.config['post']),
        )
