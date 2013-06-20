import tempfile
import webbrowser
import time
import os

class BrowserBackend(object):
    def submit_captcha(self, data):
        fd, path = tempfile.mkstemp()
        with open(path, 'w') as out:
            out.write(data)
        return path  

    def check_solution(self, captcha_id):
        image_url = 'file://' + captcha_id
        webbrowser.open(url=image_url)
        # Wait some time, skip some debug messages
        # which browser could dump to console
        time.sleep(0.5)
        solution = raw_input('Enter solution: ')
        os.unlink(captcha_id)
        return solution
