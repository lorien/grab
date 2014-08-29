import tempfile
import webbrowser
import time
import os

from grab import Grab
from grab.captcha.backend.base import CaptchaBackend

from grab.util.py3k_support import *


class BrowserBackend(CaptchaBackend):
    def get_submit_captcha_request(self, data):
        fd, path = tempfile.mkstemp()
        with open(path, 'w') as out:
            out.write(data)
        url = 'file://' + path
        g = Grab()
        g.setup(url=url)
        return g

    def parse_submit_captcha_response(self, res):
        return res.url.replace('file://', '')

    def get_check_solution_request(self, captcha_id):
        url = 'file://' + captcha_id
        g = Grab()
        g.setup(url=url)
        return g

    def parse_check_solution_response(self, res):
        webbrowser.open(url=res.url)
        # Wait some time, skip some debug messages
        # which browser could dump to console
        time.sleep(0.5)
        solution = raw_input('Enter solution: ')
        path = res.url.replace('file://', '')
        os.unlink(path)
        return solution
