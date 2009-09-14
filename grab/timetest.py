import unittest
from unittest import TestCase
import sys
import os.path
from timeit import Timer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from seo.watcher import Watcher
from grab import Grab, default_config, deepcopy, clone_config 
from grab.grab_slow import Grab as GrabSlow

CONFIG = default_config()

def main():
    g = Grab()
    #g.clone()
    g.setup(url='http://localhost/static/index.html')
    g.setup(unicode_body=False)
    g.request()

#def main2():
    #g = GrabSlow()
    #g.clone()
    #g.setup(url='http://localhost/static/index.html')
    #g.request()


if __name__ == '__main__':
    Watcher()
    t = Timer('main()', 'from __main__ import main')
    print t.timeit(number=300)
    #t = Timer('main2()', 'from __main__ import main2')
    #print t.timeit(number=300)
