# coding: utf-8
import os

from test.util import BaseGrabTestCase
from test.util import TMP_DIR, clear_directory, build_grab
from grab.base import reset_request_counter


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_log_option(self):
        clear_directory(TMP_DIR)
        reset_request_counter()

        log_file_path = os.path.join(TMP_DIR, 'log.html')
        g = build_grab()
        g.setup(log_file=log_file_path)
        self.server.response['get.data'] = 'omsk'

        self.assertEqual(os.listdir(TMP_DIR), [])
        g.go(self.server.get_url())
        self.assertEqual(os.listdir(TMP_DIR), ['log.html'])
        self.assertEqual(open(log_file_path).read(), 'omsk')

    def test_log_dir_option(self):
        clear_directory(TMP_DIR)
        reset_request_counter()

        g = build_grab()
        g.setup(log_dir=TMP_DIR)
        self.server.response_once['get.data'] = 'omsk1'
        self.server.response['get.data'] = 'omsk2'

        self.assertEqual(os.listdir(TMP_DIR), [])
        g.go(self.server.get_url())
        g.go(self.server.get_url())
        self.assertEqual(sorted(os.listdir(TMP_DIR)),
                         ['01.html', '01.log', '02.html', '02.log'])
        self.assertEqual(open(os.path.join(TMP_DIR, '01.html')).read(),
                         'omsk1')
        self.assertEqual(open(os.path.join(TMP_DIR, '02.html')).read(),
                         'omsk2')

    def test_log_dir_response_content(self):
        clear_directory(TMP_DIR)
        reset_request_counter()

        g = build_grab()
        g.setup(log_dir=TMP_DIR)
        self.server.response['get.data'] = 'omsk'
        self.server.response['headers'] = [('X-Engine', 'PHP')]

        self.assertEqual(os.listdir(TMP_DIR), [])
        g.go(self.server.get_url())
        self.assertEqual(sorted(os.listdir(TMP_DIR)), ['01.html', '01.log'])
        log_file_content = open(os.path.join(TMP_DIR, '01.log')).read()
        self.assertTrue('X-Engine' in log_file_content)

    def test_log_dir_request_content_is_empty(self):
        clear_directory(TMP_DIR)
        reset_request_counter()

        g = build_grab()
        g.setup(log_dir=TMP_DIR)
        g.setup(headers={'X-Name': 'spider'}, post='xxxPost')

        self.assertEqual(os.listdir(TMP_DIR), [])
        g.go(self.server.get_url())
        self.assertEqual(sorted(os.listdir(TMP_DIR)), ['01.html', '01.log'])
        log_file_content = open(os.path.join(TMP_DIR, '01.log')).read()
        self.assertFalse('X-Name' in log_file_content)
        self.assertFalse('xxxPost' in log_file_content)

    def test_log_dir_request_content_headers_and_post(self):
        clear_directory(TMP_DIR)
        reset_request_counter()

        g = build_grab()
        g.setup(log_dir=TMP_DIR, debug=True)
        g.setup(headers={'X-Name': 'spider'}, post={'xxx': 'Post'})

        self.assertEqual(os.listdir(TMP_DIR), [])
        g.go(self.server.get_url())
        self.assertEqual(sorted(os.listdir(TMP_DIR)), ['01.html', '01.log'])
        log_file_content = open(os.path.join(TMP_DIR, '01.log')).read()
        self.assertTrue('X-Name' in log_file_content)
        self.assertTrue('xxx=Post' in log_file_content)

    def test_debug_post(self):
        g = build_grab(debug_post=True)
        g.setup(post={'foo': 'bar'})
        self.server.response['post.data'] = 'x'
        g.go(self.server.get_url())
        self.assertEqual(b'x', g.doc.body)

    def test_debug_post_integer_bug(self):
        g = build_grab(debug_post=True)
        g.setup(post={'foo': 3})
        self.server.response['post.data'] = 'x'
        g.go(self.server.get_url())
        self.assertEqual(b'x', g.doc.body)
