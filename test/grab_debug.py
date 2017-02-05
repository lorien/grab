# coding: utf-8
import os
from mock import patch
import threading

from test.util import BaseGrabTestCase
from test.util import build_grab, exclude_grab_transport, temp_dir
from test.util import reset_request_counter
from grab.error import GrabTimeoutError


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_log_option(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            log_file_path = os.path.join(tmp_dir, 'log.html')
            g = build_grab()
            g.setup(log_file=log_file_path)
            self.server.response['get.data'] = 'omsk'

            self.assertEqual(os.listdir(tmp_dir), [])
            g.go(self.server.get_url())
            self.assertEqual(os.listdir(tmp_dir), ['log.html'])
            self.assertEqual(open(log_file_path).read(), 'omsk')

    def test_log_dir_option(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            g = build_grab()
            g.setup(log_dir=tmp_dir)
            self.server.response_once['get.data'] = 'omsk1'
            self.server.response['get.data'] = 'omsk2'

            self.assertEqual(os.listdir(tmp_dir), [])
            g.go(self.server.get_url())
            g.go(self.server.get_url())
            self.assertEqual(sorted(os.listdir(tmp_dir)),
                             ['01.html', '01.log', '02.html', '02.log'])
            self.assertEqual(open(os.path.join(tmp_dir, '01.html')).read(),
                             'omsk1')
            self.assertEqual(open(os.path.join(tmp_dir, '02.html')).read(),
                             'omsk2')

    def test_log_dir_response_content(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            g = build_grab()
            g.setup(log_dir=tmp_dir)
            self.server.response['get.data'] = 'omsk'
            self.server.response['headers'] = [('X-Engine', 'PHP')]

            self.assertEqual(os.listdir(tmp_dir), [])
            g.go(self.server.get_url())
            self.assertEqual(sorted(os.listdir(tmp_dir)), ['01.html', '01.log'])
            log_file_content = open(os.path.join(tmp_dir, '01.log')).read()
            self.assertTrue('x-engine' in log_file_content.lower())

    def test_log_dir_response_content_thread(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            g = build_grab()
            g.setup(log_dir=tmp_dir)
            self.server.response['get.data'] = 'omsk'
            self.server.response['headers'] = [('X-Engine', 'PHP')]

            self.assertEqual(os.listdir(tmp_dir), [])

            def func():
                g.go(self.server.get_url())
            th = threading.Thread(target=func)
            th.start()
            th.join()

            files = os.listdir(tmp_dir)
            self.assertEqual(2, len([x for x in files if '01-thread' in x]))
            fname = [x for x in files if x.endswith('.log')][0]
            log_file_content = open(os.path.join(tmp_dir, fname)).read()
            self.assertTrue('x-engine' in log_file_content.lower())

    @exclude_grab_transport('urllib3')
    def test_log_dir_response_network_error(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            g = build_grab()
            g.setup(log_dir=tmp_dir, timeout=1, user_agent='Perl',
                    debug=True)
            self.server.response['get.data'] = 'omsk'
            self.server.response['headers'] = [('X-Engine', 'PHP')]
            self.server.response['sleep'] = 2

            self.assertEqual(os.listdir(tmp_dir), [])
            try:
                g.go(self.server.get_url())
            except GrabTimeoutError:
                pass

            self.assertEqual(sorted(os.listdir(tmp_dir)), ['01.html', '01.log'])
            log_file_content = open(os.path.join(tmp_dir, '01.log')).read()
            self.assertTrue('user-agent: perl' in log_file_content.lower())


    def test_log_dir_request_content_is_empty(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            g = build_grab()
            g.setup(log_dir=tmp_dir)
            g.setup(headers={'X-Name': 'spider'}, post='xxxPost')

            self.assertEqual(os.listdir(tmp_dir), [])
            g.go(self.server.get_url())
            self.assertEqual(sorted(os.listdir(tmp_dir)), ['01.html', '01.log'])
            log_file_content = open(os.path.join(tmp_dir, '01.log')).read()
            self.assertFalse('X-Name' in log_file_content)
            self.assertFalse('xxxPost' in log_file_content)

    # because urllib3 does not collects request headers
    @exclude_grab_transport('urllib3')
    def test_log_dir_request_content_headers_and_post(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            g = build_grab()
            g.setup(log_dir=tmp_dir, debug=True)
            g.setup(headers={'X-Name': 'spider'}, post={'xxx': 'Post'})

            self.assertEqual(os.listdir(tmp_dir), [])
            g.go(self.server.get_url())
            self.assertEqual(sorted(os.listdir(tmp_dir)), ['01.html', '01.log'])
            log_file_content = open(os.path.join(tmp_dir, '01.log')).read()
            #if not 'x-name' in log_file_content.lower():
            #    print('CONTENT OF 01.log:')
            #    print(log_file_content)
            self.assertTrue('x-name' in log_file_content.lower())
            self.assertTrue('xxx=post' in log_file_content.lower())

    def test_debug_post(self):
        g = build_grab(debug_post=True)
        g.setup(post={'foo': 'bar'})
        self.server.response['post.data'] = 'x'
        g.go(self.server.get_url())
        self.assertEqual(b'x', g.doc.body)

    def test_debug_nonascii_post(self):
        g = build_grab(debug=True)
        g.setup(post=u'фыва'.encode('cp1251'))
        g.go(self.server.get_url())

    def test_debug_nonascii_multipart_post(self):
        g = build_grab(debug=True)
        g.setup(charset='cp1251', multipart_post=[('x', u'фыва'.encode('cp1251'))])
        g.go(self.server.get_url())

    def test_debug_post_integer_bug(self):
        g = build_grab(debug_post=True)
        g.setup(post={'foo': 3})
        self.server.response['post.data'] = 'x'
        g.go(self.server.get_url())
        self.assertEqual(b'x', g.doc.body)

    def test_debug_post_big_str(self):
        g = build_grab(debug_post=True)
        big_value = 'x' * 1000
        g.setup(post=big_value)
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['data'], big_value.encode())

    def test_debug_post_dict_big_value(self):
        g = build_grab(debug_post=True)
        big_value = 'x' * 1000
        g.setup(post={
            'foo': big_value,
        })
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['data'], ('foo=%s' % big_value).encode())

    def test_log_request_extra_argument(self):
        import grab.base

        g = build_grab()
        g.go(self.server.get_url())
        with patch.object(grab.base.logger_network, 'debug') as mocked:
            g.log_request()
            args = mocked.mock_calls[0][1]
            self.assertEqual('', args[3])

        with patch.object(grab.base.logger_network, 'debug') as mocked:
            g.log_request(extra='zz')
            args = mocked.mock_calls[0][1]
            self.assertEqual('[zz] ', args[3])
