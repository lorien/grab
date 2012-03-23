import pygtk
pygtk.require('2.0')
import gtk
import os
from StringIO import StringIO
import tempfile

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


def solve_captcha(data, key=None):
    fobj = StringIO(data)
    solution = []
    fh, path = tempfile.mkstemp()
    open(path, 'w').write(fobj.read())
    window = CaptchaWindow(path, solution)
    window.main()
    os.unlink(path)
    return solution[0]
