# coding: utf-8
import re

from weblib.error import DataNotFound

from tests.util import build_grab, temp_file
from tests.util import BaseGrabTestCase
from grab.error import GrabMisuseError


class GrabApiTestCase(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        import grab.util.warning

        grab.util.warning.DISABLE_WARNINGS = True
        super(GrabApiTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        import grab.util.warning

        grab.util.warning.DISABLE_WARNINGS = False
        super(GrabApiTestCase, cls).tearDownClass()

    def setUp(self):
        self.server.reset()

    def test_choose_form_by_element(self):
        data = b'''
        <form><input name="foo"></form>
        <form><input name="bar"></form>
        '''
        grab = build_grab(data)
        grab.choose_form_by_element('//input[@name="bar"]')
        self.assertEqual(
            grab.doc('//form[2]').node(),
            grab.doc.form)

    def test_choose_form_by_element_noform(self):
        data = b'''
        <div>test</div>
        '''
        grab = build_grab(data)
        self.assertRaises(DataNotFound, grab.choose_form_by_element,
                          '//input[@name="bar"]')

    def test_form_fields(self):
        data = b'''
        <form>
            <input value="foo">
            <input name="dis" disabled="disabled" value="diz">
            <select name="sel">
                <option value="opt1">opt1</option)
                <option value="opt2">opt2</option)
            </select>
            <input type="radio" name="rad1" value="rad1">
            <input type="checkbox" name="cb1" value="cb1">
            <input type="checkbox" name="cb2" value="cb2" checked="checked">
            <input type="text" name="text1" value="text1">
            <textarea name="area1">area1</textarea>
        </form>
        '''
        grab = build_grab(data)
        fields = {
            'sel': 'opt1',
            'rad1': 'rad1',
            'cb2': 'cb2',
            'text1': 'text1',
            'area1': 'area1',
        }
        self.assertEqual(fields, grab.form_fields())

    def test_submit(self):
        data = b'''<form method="post">
            <input type="text" name="foo" value="val"></form>'''
        grab = build_grab(data)
        grab.choose_form(0)
        grab.submit(make_request=False)
        self.assertTrue('foo' in dict(grab.config['post']))

    def test_set_input_methods(self):
        data = b'''<form><input type="text" id="f" name="foo" value="val">
            </form>'''
        grab = build_grab(data)
        grab.set_input_by_id('f', 'new')
        self.assertEqual(grab.doc('//input/@value').text(), 'new')
        grab.set_input_by_number(0, 'new2')
        self.assertEqual(grab.doc('//input/@value').text(), 'new2')
        grab.set_input_by_xpath('//input[@name="foo"]', 'new3')
        self.assertEqual(grab.doc('//input/@value').text(), 'new3')
        grab.set_input('foo', 'new4')
        self.assertEqual(grab.doc('//input/@value').text(), 'new4')

    def test_form(self):
        data = b'''<form><input type="text" id="f" name="foo" value="val">
            </form>'''
        grab = build_grab(data)
        self.assertEqual(grab.doc('//form').node(), grab.doc.form)

    def test_load_proxylist_text_file(self):
        with temp_file() as proxy_file:
            with open(proxy_file, 'w') as out:
                out.write('1.1.1.1:8080')
            grab = build_grab()
            grab.load_proxylist(proxy_file, 'text_file', auto_init=True,
                                auto_change=False)
            self.assertEqual(grab.config['proxy'], '1.1.1.1:8080')

    def test_load_proxylist_url(self):
        self.server.response['data'] = b'1.1.1.1:9090'
        grab = build_grab()
        grab.load_proxylist(self.server.get_url(), 'url',
                            auto_init=True, auto_change=False)
        self.assertEqual(grab.config['proxy'], '1.1.1.1:9090')

    def test_load_proxylist_invalid_input(self):
        grab = build_grab()
        self.assertRaises(GrabMisuseError, grab.load_proxylist,
                          None, 'zzz')

    def test_response_property(self):
        grab = build_grab()
        self.assertEqual(grab.doc, grab.doc)
        grab.doc = grab.doc
        self.assertEqual(grab.doc, grab.doc)

    def test_pyquery(self):
        data = b'''<form><input type="text" id="f" name="foo" value="val">
            </form>'''
        grab = build_grab(data)
        # pylint: disable=no-member
        self.assertEqual(grab.doc('//input').node().value,
                         grab.pyquery('input')[0].value)
        # pylint: enable=no-member

    def test_assert_xpath(self):
        data = b'''<h1>tet</h1>'''
        grab = build_grab(data)
        grab.assert_xpath('//h1')
        self.assertRaises(DataNotFound, grab.assert_xpath, '//h2')

    def test_assert_css(self):
        data = b'''<h1>tet</h1>'''
        grab = build_grab(data)
        grab.assert_css('h1')
        self.assertRaises(DataNotFound, grab.assert_css, 'h2')

    def test_css(self):
        data = b'''<h1>tet</h1>'''
        grab = build_grab(data)
        self.assertEqual(grab.doc('//h1').node(), grab.css('h1'))

    def test_xpath(self):
        data = b'''<h1>tet</h1>'''
        grab = build_grab(data)
        self.assertEqual(grab.doc('//h1').node(), grab.xpath('//h1'))

    def test_find_link_rex(self):
        data = b'''<a href="http://ya.ru/">ya.ru</a>'''
        grab = build_grab(data)
        self.assertEqual('http://ya.ru/',
                         grab.find_link_rex(re.compile(r'ya\.ru'),
                                            make_absolute=True))
        self.assertEqual(None,
                         grab.find_link_rex(re.compile(r'google\.ru'),
                                            make_absolute=True))

    def test_find_link(self):
        data = b'''<a href="http://ya.ru/">ya.ru</a>'''
        grab = build_grab(data)
        self.assertEqual('http://ya.ru/',
                         grab.find_link(b'ya.ru',
                                        make_absolute=True))
        self.assertEqual(None,
                         grab.find_link(b'google.ru',
                                        make_absolute=True))
        self.assertRaises(GrabMisuseError, grab.find_link,
                          u'asdf')

    def test_build_html_tree(self):
        data = b'<div>test</div>'
        grab = build_grab(data)
        self.assertEqual(grab.doc.tree, grab.build_html_tree())

    def test_build_xml_tree(self):
        data = b'<div>test</div>'
        grab = build_grab(data, content_type='xml')
        self.assertEqual(grab.doc.tree, grab.build_xml_tree())
