# coding: utf-8
from tools.etree import parse_html
from tools.error import DataNotFound

from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_choose_form_by_element(self):
        data = '''
        <form><input name="foo"></form>
        <form><input name="bar"></form>
        '''
        g = build_grab(data)
        g.choose_form_by_element('//input[@name="bar"]')
        self.assertEqual(
            g.doc('//form[2]').node(),
            g.doc.form)

    def test_choose_form_by_element_noform(self):
        data = '''
        <div>test</div>
        '''
        g = build_grab(data)
        self.assertRaises(DataNotFound, g.choose_form_by_element,
                          '//input[@name="bar"]')
