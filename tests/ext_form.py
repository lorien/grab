# coding: utf-8
try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from grab import DataNotFound, GrabMisuseError
from tests.util import build_grab
from tests.util import BaseGrabTestCase

FORMS_HTML = u"""
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
        self.grab = build_grab()
        self.grab.setup_document(FORMS_HTML)

    def test_choose_form(self):
        """
        Test ``choose_form`` method
        """

        # raise errors
        self.assertRaises(DataNotFound, self.grab.doc.choose_form, 10)
        self.assertRaises(DataNotFound, self.grab.doc.choose_form, id='bad_id')
        self.assertRaises(DataNotFound, self.grab.doc.choose_form,
                          id='fake_form')
        self.assertRaises(GrabMisuseError, self.grab.doc.choose_form)

        # check results
        self.grab.doc.choose_form(0)
        # pylint: disable=no-member,protected-access
        self.assertEqual('form', self.grab.doc._lxml_form.tag)
        self.assertEqual('search_form', self.grab.doc._lxml_form.get('id'))
        # pylint: enable=no-member,protected-access

        # reset current form
        self.grab.doc._lxml_form = None # pylint: disable=protected-access

        self.grab.doc.choose_form(id='common_form')
        # pylint: disable=no-member,protected-access
        self.assertEqual('form', self.grab.doc._lxml_form.tag)
        self.assertEqual('common_form', self.grab.doc._lxml_form.get('id'))
        # pylint: enable=no-member,protected-access

        # reset current form
        self.grab.doc._lxml_form = None # pylint: disable=protected-access

        self.grab.doc.choose_form(name='dummy')
        # pylint: disable=no-member,protected-access
        self.assertEqual('form', self.grab.doc._lxml_form.tag)
        self.assertEqual('dummy', self.grab.doc._lxml_form.get('name'))
        # pylint: enable=no-member,protected-access

        # reset current form
        self.grab.doc._lxml_form = None # pylint: disable=protected-access

        self.grab.doc.choose_form(xpath='//form[contains(@action, "/dummy")]')
        # pylint: disable=no-member,protected-access
        self.assertEqual('form', self.grab.doc._lxml_form.tag)
        self.assertEqual('dummy', self.grab.doc._lxml_form.get('name'))
        # pylint: enable=no-member,protected-access

    def assert_equal_qs(self, qs1, qs2):
        args1 = set([(x, y) for x, y in parse_qsl(qs1)])
        args2 = set([(x, y) for x, y in parse_qsl(qs2)])
        self.assertEqual(args1, args2)

    def test_submit(self):
        grab = build_grab()
        self.server.response['get.data'] = POST_FORM % self.server.get_url()
        grab.go(self.server.get_url())
        grab.doc.set_input('name', 'Alex')
        grab.doc.submit()
        self.assert_equal_qs(self.server.request['data'],
                             b'name=Alex&secret=123')

        # Default submit control
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM
        grab.go(self.server.get_url())
        grab.doc.submit()
        self.assert_equal_qs(self.server.request['data'],
                             b'secret=123&submit1=submit1')

        # Selected submit control
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM
        grab.go(self.server.get_url())
        grab.doc.submit(submit_name='submit2')
        self.assert_equal_qs(self.server.request['data'],
                             b'secret=123&submit2=submit2')

        # Default submit control if submit control name is invalid
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM
        grab.go(self.server.get_url())
        grab.doc.submit(submit_name='submit3')
        self.assert_equal_qs(self.server.request['data'],
                             b'secret=123&submit1=submit1')

    def test_submit_remove_from_post_argument(self):
        grab = build_grab()
        self.server.response['get.data'] = MULTIPLE_SUBMIT_FORM

        grab.go(self.server.get_url())
        grab.doc.submit(submit_name='submit3')
        self.assert_equal_qs(self.server.request['data'],
                             b'secret=123&submit1=submit1')

        grab.go(self.server.get_url())
        grab.doc.submit(remove_from_post=['submit1'])
        self.assert_equal_qs(self.server.request['data'],
                             b'secret=123')

    def test_set_methods(self):
        grab = build_grab()
        self.server.response['get.data'] = FORMS_HTML
        grab.go(self.server.get_url())

        # pylint: disable=protected-access
        self.assertEqual(grab.doc._lxml_form, None)
        # pylint: enable=protected-access

        grab.doc.set_input('gender', '1')
        # pylint: disable=no-member,protected-access
        self.assertEqual('common_form', grab.doc._lxml_form.get('id'))
        # pylint: enable=no-member,protected-access

        # pylint: disable=no-member,protected-access
        self.assertRaises(KeyError,
                          lambda: grab.doc.set_input('query', 'asdf'))
        # pylint: enable=no-member,protected-access

        grab.doc._lxml_form = None # pylint: disable=protected-access
        grab.doc.set_input_by_id('search_box', 'asdf')
        # pylint: disable=no-member,protected-access
        self.assertEqual('search_form', grab.doc._lxml_form.get('id'))
        # pylint: enable=no-member,protected-access

        grab.doc.choose_form(xpath='//form[@id="common_form"]')
        grab.doc.set_input_by_number(0, 'asdf')

        # pylint: disable=no-member,protected-access
        grab.doc._lxml_form = None
        grab.doc.set_input_by_xpath('//*[@name="gender"]', '2')
        self.assertEqual('common_form', grab.doc._lxml_form.get('id'))
        # pylint: enable=no-member,protected-access

    def test_html_without_forms(self):
        grab = build_grab()
        self.server.response['get.data'] = NO_FORM_HTML
        grab.go(self.server.get_url())
        self.assertRaises(DataNotFound, lambda: grab.doc.form)

    def test_disabled_radio(self):
        """
        Bug #57
        """

        grab = build_grab()
        self.server.response['get.data'] = DISABLED_RADIO_HTML
        grab.go(self.server.get_url())
        grab.doc.submit(make_request=False)

    def test_set_input_by_xpath_regex(self):
        html = b'''
            <div><form action="" method="post"><input name="foo" type="text">
            <input name="bar" id="bar" type="text">
        '''
        grab = build_grab(html)
        grab.doc.set_input_by_xpath('//input[re:test(@id, "^ba")]',
                                    'bar-value')
        grab.doc.submit(make_request=False)
        self.assertEqual(
            set([('foo', None), ('bar', 'bar-value')]),
            set(grab.config['post']),
        )

    def test_unicode_textarea_form(self):
        html = u'''
            <form enctype="multipart/form-data" action=""
                method="post" accept-charset="UTF-8">
                <textarea name="body">Beställa</textarea>
                <input type="submit" name="op" value="Save"/>
            </form>
        '''.encode('utf-8')
        self.server.response['get.data'] = html
        grab = build_grab()
        grab.go(self.server.get_url())
        grab.doc.submit()
        self.assertTrue(u'Beställa'.encode('utf-8')
                        in self.server.request['data'])
