#!/usr/bin/env python
# coding: utf-8
import unittest
from unittest import TestCase
import re
import threading
import time
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urllib

import logging
logging.basicConfig(level=logging.DEBUG)

from grab import Grab, GrabMisuseError, DataNotFound, UploadContent

# The port on which the fake http server listens requests
FAKE_SERVER_PORT = 9876

# Simple URL which could be used in tests
BASE_URL = 'http://localhost:%d' % FAKE_SERVER_PORT

# This global objects is used by Fake HTTP Server
# It return content of HTML variable for any GET request
RESPONSE = {'get': '', 'post': ''}

# Fake HTTP Server saves request details
# into global REQUEST variable
REQUEST = {'get': None, 'post': None, 'headers': None}

class FakeServerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(FakeServerThread, self).__init__(*args, **kwargs)
        self.daemon = True

    def start(self):
        super(FakeServerThread, self).start()
        time.sleep(0.1)

    def run(self):
        # TODO: reset REQUEST before each get/post request
        class RequestHandlerClass(BaseHTTPRequestHandler):
            def do_GET(self):
                """
                Process GET request.

                Reponse body contains content from ``RESPONSE['get']``
                """

                self.send_response(200)
                self.end_headers()
                self.wfile.write(RESPONSE['get'])
                REQUEST['headers'] = self.headers

            def log_message(*args, **kwargs):
                "Do not log to console"
                pass

            def do_POST(self):
                post_size = int(self.headers.getheader('content-length'))
                REQUEST['post'] = self.rfile.read(post_size)
                REQUEST['headers'] = self.headers
                self.send_response(200)
                self.end_headers()
                self.wfile.write(RESPONSE['post'])

        server_address = ('localhost', FAKE_SERVER_PORT)
        try:
            httpd = HTTPServer(server_address, RequestHandlerClass)
            httpd.serve_forever()
        except IOError:
            # Do nothing if server alrady is running
            pass


HTML = u"""
<head>
    <title>фыва</title>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251" />
</head>
<body>
    <div id="bee">
        <div class="wrapper">
            <strong id="bee-strong">пче</strong><em id="bee-em">ла</em>
        </div>
        <script type="text/javascript">
        mozilla = 777;
        </script>
        <style type="text/css">
        body { color: green; }
        </style>
    </div>
    <div id="fly">
        <strong id="fly-strong">му\n</strong><em id="fly-em">ха</em>
    </div>
    <ul id="num">
        <li id="num-1">item #100 2</li>
        <li id="num-2">item #2</li>
    </ul>
""".encode('cp1251')

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
        <form name="dummy">
           <input type="submit" value="submit" class="submit_btn" name="submit" />
        </form>
    </div>
</body>
""".encode('utf-8')

class TextExtensionTest(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.response.body = HTML
        self.g.response.charset = 'cp1251'

    def test_search(self):
        self.assertTrue(self.g.search(u'фыва'.encode('cp1251'), byte=True))
        self.assertTrue(self.g.search(u'фыва'))
        self.assertFalse(self.g.search(u'фыва2'))

    def test_search_usage_errors(self):
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search(u'фыва', byte=True))
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search('фыва'))

    def test_search_rex(self):
        # Search unicode rex in unicode body - default case
        rex = re.compile(u'фыва', re.U)
        self.assertEqual(u'фыва', self.g.search_rex(rex).group(0))

        # Search non-unicode rex in byte-string body
        rex = re.compile(u'фыва'.encode('cp1251'))
        self.assertEqual(u'фыва'.encode('cp1251'), self.g.search_rex(rex, byte=True).group(0))

        # Search for non-unicode rex in unicode body shuld fail
        rex = re.compile('фыва')
        self.assertEqual(None, self.g.search_rex(rex))

        # Search for unicode rex in byte-string body shuld fail
        rex = re.compile(u'фыва', re.U)
        self.assertEqual(None, self.g.search_rex(rex, byte=True))

        # Search for unexesting fragment
        rex = re.compile(u'фыва2', re.U)
        self.assertEqual(None, self.g.search_rex(rex))

    def test_assert_substring(self):
        self.g.assert_substring(u'фыва')
        self.g.assert_substring(u'фыва'.encode('cp1251'), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_substring(u'фыва2'))

    def test_assert_substrings(self):
        self.g.assert_substrings((u'фыва',))
        self.g.assert_substrings((u'фывы нет', u'фыва'))
        self.g.assert_substrings((u'фыва'.encode('cp1251'), 'где ты фыва?'), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_substrings((u'фыва, вернись', u'фыва-а-а-а')))

    def test_assert_rex(self):
        self.g.assert_rex(re.compile(u'фыва'))
        self.g.assert_rex(re.compile(u'фыва'.encode('cp1251')), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_rex(re.compile(u'фыва2')))

    def test_find_number(self):
        self.assertEqual('2', self.g.find_number('2'))
        self.assertEqual('2', self.g.find_number('foo 2 4 bar'))
        self.assertEqual('24', self.g.find_number('foo 2 4 bar', ignore_spaces=True))
        self.assertEqual('24', self.g.find_number(u'бешеный 2 4 барсук', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.find_number('foo'))
        self.assertRaises(DataNotFound,
            lambda: self.g.find_number(u'фыва'))

    def test_drop_space(self):
        self.assertEqual('', self.g.drop_space(' '))
        self.assertEqual('f', self.g.drop_space(' f '))
        self.assertEqual('fb', self.g.drop_space(' f b '))
        self.assertEqual(u'триглаза', self.g.drop_space(u' тр и гла' + '\t' + '\n' + u' за '))


class LXMLExtensionTest(unittest.TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.response.body = HTML
        self.g.response.charset = 'cp1251'

        from lxml.html import fromstring
        self.lxml_tree = fromstring(self.g.response.body)

    def test_lxml_text_content_fail(self):
        # lxml node text_content() method do not put spaces between text
        # content of adjacent XML nodes
        self.assertEqual(self.lxml_tree.xpath('//div[@id="bee"]/div')[0].text_content().strip(), u'пчела')
        self.assertEqual(self.lxml_tree.xpath('//div[@id="fly"]')[0].text_content().strip(), u'му\nха')

    def test_lxml_xpath(self):
        names = set(x.tag for x in self.lxml_tree.xpath('//div[@id="bee"]//*'))
        self.assertEqual(set(['em', 'div', 'strong', 'style', 'script']), names)
        names = set(x.tag for x in self.lxml_tree.xpath('//div[@id="bee"]//*[name() != "script" and name() != "style"]'))
        self.assertEqual(set(['em', 'div', 'strong']), names)

    def test_get_node_text(self):
        elem = self.lxml_tree.xpath('//div[@id="bee"]')[0]
        self.assertEqual(self.g.get_node_text(elem), u'пче ла')
        elem = self.lxml_tree.xpath('//div[@id="fly"]')[0]
        self.assertEqual(self.g.get_node_text(elem), u'му ха')

    def test_find_node_number(self):
        node = self.lxml_tree.xpath('//li[@id="num-1"]')[0]
        self.assertEqual('100', self.g.find_node_number(node))
        self.assertEqual('1002', self.g.find_node_number(node, ignore_spaces=True))

    def test_xpath(self):
        self.assertEqual('bee-em', self.g.xpath('//em').get('id'))
        self.assertEqual('num-2', self.g.xpath(u'//*[text() = "item #2"]').get('id'))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath('//em[@id="baz"]'))
        self.assertEqual(None, self.g.xpath('//zzz', default=None))
        self.assertEqual('foo', self.g.xpath('//zzz', default='foo'))

    def test_xpath_text(self):
        self.assertEqual(u'пче ла', self.g.xpath_text('//*[@id="bee"]'))
        self.assertEqual(u'пче ла му ха item #100 2 item #2', self.g.xpath_text('/html/body'))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath_text('//code'))
        self.assertEqual(u'bee', self.g.xpath('//*[@id="bee"]/@id'))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath_text('//*[@id="bee2"]/@id'))

    def test_xpath_number(self):
        self.assertEqual('100', self.g.xpath_number('//li'))
        self.assertEqual('1002', self.g.xpath_number('//li', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath_number('//liza'))
        self.assertEqual('foo', self.g.xpath_number('//zzz', default='foo'))

    def test_xpath_list(self):
        self.assertEqual(['num-1', 'num-2'],
            [x.get('id') for x in self.g.xpath_list('//li')])

    def test_css(self):
        self.assertEqual('bee-em', self.g.css('em').get('id'))
        self.assertEqual('num-2', self.g.css('#num-2').get('id'))
        self.assertRaises(DataNotFound,
            lambda: self.g.css('em#baz'))
        self.assertEqual('foo', self.g.css('zzz', default='foo'))

    def test_css_text(self):
        self.assertEqual(u'пче ла', self.g.css_text('#bee'))
        self.assertEqual(u'пче ла му ха item #100 2 item #2', self.g.css_text('html body'))
        self.assertRaises(DataNotFound,
            lambda: self.g.css_text('code'))
        self.assertEqual('foo', self.g.css_text('zzz', default='foo'))

    def test_css_number(self):
        self.assertEqual('100', self.g.css_number('li'))
        self.assertEqual('1002', self.g.css_number('li', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.css_number('liza'))
        self.assertEqual('foo', self.g.css_number('zzz', default='foo'))

    def test_css_list(self):
        self.assertEqual(['num-1', 'num-2'],
            [x.get('id') for x in self.g.css_list('li')])

    def test_strip_tags(self):
        self.assertEqual('foo', self.g.strip_tags('<b>foo</b>'))
        self.assertEqual('foo bar', self.g.strip_tags('<b>foo</b> <i>bar'))
        self.assertEqual('foo bar', self.g.strip_tags('<b>foo</b><i>bar'))
        self.assertEqual('', self.g.strip_tags('<b> <div>'))


class TestHtmlForms(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.response.body = FORMS
        self.g.response.charset = 'utf-8'

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



class TestFakeServer(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_get(self):
        RESPONSE['get'] = 'zorro'
        data = urllib.urlopen(BASE_URL).read()
        self.assertEqual(data, RESPONSE['get'])

    def test_post(self):
        RESPONSE['post'] = 'foo'
        data = urllib.urlopen(BASE_URL, 'THE POST').read()
        self.assertEqual(data, RESPONSE['post'])


class TestGrab(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_basic(self):
        RESPONSE['get'] = 'the cat'
        g = Grab()
        g.go(BASE_URL)
        self.assertEqual('the cat', g.response.body)

    def test_xml_with_declaration(self):
        RESPONSE['get'] = '<?xml version="1.0" encoding="UTF-8"?><root><foo>foo</foo></root>'
        g = Grab()
        g.go(BASE_URL)
        self.assertTrue(g.xpath('//foo').text == 'foo')

    def test_incorrect_option_name(self):
        g = Grab()
        self.assertRaises(GrabMisuseError,
            lambda: g.setup(save_the_word=True))


class TestPostFeature(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_post(self):
        g = Grab(url=BASE_URL, debug_post=True)

        # Provide POST data in dict
        g.setup(post={'foo': 'bar'})
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=bar')

        # Provide POST data in tuple
        g.setup(post=(('foo', 'TUPLE'),))
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=TUPLE')

        # Provide POST data in list
        g.setup(post=[('foo', 'LIST')])
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=LIST')

        # Provide POST data in byte-string
        g.setup(post='Hello world!')
        g.request()
        self.assertEqual(REQUEST['post'], 'Hello world!')

        # Provide POST data in unicode-string
        g.setup(post=u'Hello world!')
        g.request()
        self.assertEqual(REQUEST['post'], 'Hello world!')

        # Provide POST data in non-ascii unicode-string
        g.setup(post=u'Привет, мир!')
        g.request()
        self.assertEqual(REQUEST['post'], 'Привет, мир!')

        # Two values with one key
        g.setup(post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=bar&foo=baz')

        # Few values with non-ascii data
        # TODO: understand and fix
        # AssertionError: 'foo=bar&gaz=%D0%94%D0%B5%D0%BB%D1%8C%D1%84%D0%B8%D0%BD&abc=' != 'foo=bar&gaz=\xd0\x94\xd0\xb5\xd0\xbb\xd1\x8c\xd1\x84\xd0\xb8\xd0\xbd&abc='
        #g.setup(post=({'foo': 'bar', 'gaz': u'Дельфин', 'abc': None}))
        #g.request()
        #self.assertEqual(REQUEST['post'], 'foo=bar&gaz=Дельфин&abc=')

        # Multipart data could not be dict or string
        g.setup(multipart_post={'foo': 'bar'})
        self.assertRaises(GrabMisuseError, lambda: g.request())
        g.setup(multipart_post='asdf')
        self.assertRaises(GrabMisuseError, lambda: g.request())

        # tuple with one pair
        g.setup(multipart_post=(('foo', 'bar'),))
        g.request()
        self.assertTrue('name="foo"' in REQUEST['post'])

        # tuple with two pairs
        g.setup(multipart_post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertTrue('name="foo"' in REQUEST['post'])

class TestProxy(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_proxy(self):
        g = Grab()
        proxy = 'localhost:%d' % FAKE_SERVER_PORT 
        g.setup(proxy=proxy, proxy_type='http')
        RESPONSE['get'] = '123'
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_proxylist(self):
        g = Grab()
        proxy = 'localhost:%d' % FAKE_SERVER_PORT 
        open('/tmp/__proxy.txt', 'w').write(proxy)
        g.setup_proxylist('/tmp/__proxy.txt', 'http')
        RESPONSE['get'] = '123'
        g.change_proxy()
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])


class TestUploadContent(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.response.body = FORMS
        self.g.response.charset = 'utf-8'

    def test(self):
        fc = UploadContent('a')
        self.assertEqual(fc, 'xxx')
        self.g.set_input('image', fc)

if __name__ == '__main__':
    unittest.main()
