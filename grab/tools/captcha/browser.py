import webbrowser
import os
from StringIO import StringIO
import time

def solve_captcha(fobj, key=None):
    if isinstance(fobj, str):
        fobj = StringIO(fobj)
    solution = []
    path = os.tmpnam() + '.jpg'
    open(path, 'w').write(fobj.read())
    webbrowser.open_new_tab('file://' + path)
    time.sleep(0.5)
    return raw_input('Solution: ')
