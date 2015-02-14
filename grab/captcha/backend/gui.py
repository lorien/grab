import tempfile
import webbrowser
import time
import os
import pygtk
import gtk
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from grab import Grab
from grab.captcha.backend.base import CaptchaBackend

pygtk.require('2.0')

class CaptchaWindow(object):
    def __init__(self, path, solution):
        self.solution = solution
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.show()
        self.window.connect('destroy', self.destroy)
        self.box = gtk.HBox()
        self.image = gtk.Image()
        self.image.set_from_file(path)
        self.entry = gtk.Entry()
        self.entry.connect('activate', self.solve)
        self.button = gtk.Button('Go')
        self.button.connect('clicked', self.solve)

        self.window.add(self.box)
        self.box.pack_start(self.image)
        self.box.pack_start(self.entry)
        self.box.pack_start(self.button)
        self.box.show()
        self.image.show()
        self.button.show()
        self.entry.show()
        self.entry.grab_focus()

    def destroy(self, *args):
        gtk.main_quit()

    def solve(self, *args):
        self.solution.append(self.entry.get_text())
        self.window.hide()
        gtk.main_quit()

    def main(self):
        gtk.main()


class GuiBackend(CaptchaBackend):
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
        path = res.url.replace('file://', '')
        solution = []
        window = CaptchaWindow(path, solution)
        window.main()
        os.unlink(path)
        return solution[0]
