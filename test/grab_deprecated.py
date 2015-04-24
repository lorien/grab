# coding: utf-8
from weblib.etree import parse_html
from weblib.error import DataNotFound
from grab.error import GrabMisuseError
from tempfile import mkstemp
import os
import re

from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_choose_form_by_element(self):
        data = b'''
        <form><input name="foo"></form>
        <form><input name="bar"></form>
        '''
        g = build_grab(data)
        g.choose_form_by_element('//input[@name="bar"]')
        self.assertEqual(
            g.doc('//form[2]').node(),
            g.doc.form)

    def test_choose_form_by_element_noform(self):
        data = b'''
        <div>test</div>
        '''
        g = build_grab(data)
        self.assertRaises(DataNotFound, g.choose_form_by_element,
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
        g = build_grab(data)
        fields = {
            'sel': 'opt1',
            'rad1': 'rad1',
            'cb2': 'cb2',
            'text1': 'text1',
            'area1': 'area1',
        }
        self.assertEqual(fields, g.form_fields())

    def test_submit(self):
        data = b'''<form method="post">
            <input type="text" name="foo" value="val"></form>'''
        g = build_grab(data)
        g.choose_form(0)
        g.submit(make_request=False)
        self.assertTrue('foo' in dict(g.config['post']))

    def test_set_input_methods(self):
        data = b'''<form><input type="text" id="f" name="foo" value="val">
            </form>'''
        g = build_grab(data)
        g.set_input_by_id('f', 'new')
        self.assertEqual(g.doc('//input/@value').text(), 'new')
        g.set_input_by_number(0, 'new2')
        self.assertEqual(g.doc('//input/@value').text(), 'new2')
        g.set_input_by_xpath('//input[@name="foo"]', 'new3')
        self.assertEqual(g.doc('//input/@value').text(), 'new3')
        g.set_input('foo', 'new4')
        self.assertEqual(g.doc('//input/@value').text(), 'new4')

    def test_form(self):
        data = b'''<form><input type="text" id="f" name="foo" value="val">
            </form>'''
        g = build_grab(data)
        self.assertEqual(g.doc('//form').node(), g.form)

    def test_load_proxylist_text_file(self):
        fh, path = mkstemp()
        with open(path, 'w') as out:
            out.write('1.1.1.1:8080')
        g = build_grab()
        g.load_proxylist(path, 'text_file', auto_init=True, auto_change=False)
        self.assertEqual(g.config['proxy'], '1.1.1.1:8080')
        os.unlink(path)

    def test_load_proxylist_url(self):
        self.server.response['data'] = b'1.1.1.1:9090'
        g = build_grab()
        g.load_proxylist(self.server.get_url(), 'url',
                         auto_init=True, auto_change=False)
        self.assertEqual(g.config['proxy'], '1.1.1.1:9090')

    def test_load_proxylist_invalid_input(self):
        g = build_grab()
        self.assertRaises(GrabMisuseError, g.load_proxylist,
                          None, 'zzz')

    def test_response_property(self):
        g = build_grab()
        self.assertEqual(g.response, g.doc)
        g.response = g.doc
        self.assertEqual(g.response, g.doc)

    def test_pyquery(self):
        data = b'''<form><input type="text" id="f" name="foo" value="val">
            </form>'''
        g = build_grab(data)
        self.assertEqual(g.doc('//input').node().value,
                         g.pyquery('input')[0].value)

    def test_assert_xpath(self):
        data = b'''<h1>tet</h1>'''
        g = build_grab(data)
        g.assert_xpath('//h1')
        self.assertRaises(DataNotFound, g.assert_xpath, '//h2')

    def test_assert_css(self):
        data = b'''<h1>tet</h1>'''
        g = build_grab(data)
        g.assert_css('h1')
        self.assertRaises(DataNotFound, g.assert_css, 'h2')

    def test_deprecated_filter_argument(self):
        data = b'''<h1>tet</h1>'''
        g = build_grab(data)
        self.assertRaises(GrabMisuseError, g.xpath_number, '//h1',
                          filter=lambda: True)
        self.assertRaises(GrabMisuseError, g.xpath_text, '//h1',
                          filter=lambda: True)
        self.assertRaises(GrabMisuseError, g.xpath_list, '//h1',
                          filter=lambda: True)
        self.assertRaises(GrabMisuseError, g.xpath_one, '//h1',
                          filter=lambda: True)
        self.assertRaises(GrabMisuseError, g.xpath, '//h1',
                          filter=lambda: True)

    def test_css(self):
        data = b'''<h1>tet</h1>'''
        g = build_grab(data)
        self.assertEqual(g.doc('//h1').node(), g.css('h1'))

    def test_xpath(self):
        data = b'''<h1>tet</h1>'''
        g = build_grab(data)
        self.assertEqual(g.doc('//h1').node(), g.xpath('//h1'))

    def test_find_link_rex(self):
        data = b'''<a href="http://ya.ru/">ya.ru</a>'''
        g = build_grab(data)
        self.assertEqual('http://ya.ru/',
                         g.find_link_rex(re.compile('ya\.ru'),
                                         make_absolute=True))
        self.assertEqual(None,
                         g.find_link_rex(re.compile('google\.ru'),
                                         make_absolute=True))

    def test_find_link(self):
        data = b'''<a href="http://ya.ru/">ya.ru</a>'''
        g = build_grab(data)
        self.assertEqual('http://ya.ru/',
                         g.find_link(b'ya.ru',
                                     make_absolute=True))
        self.assertEqual(None,
                         g.find_link(b'google.ru',
                                     make_absolute=True))
        self.assertRaises(GrabMisuseError, g.find_link,
                          u'asdf')

    def test_build_html_tree(self):
        data = b'<div>test</div>'
        g = build_grab(data)
        self.assertEqual(g.doc.tree, g.build_html_tree())

    def test_build_xml_tree(self):
        data = b'<div>test</div>'
        g = build_grab(data, content_type='xml')
        self.assertEqual(g.doc.tree, g.build_xml_tree())
