# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError

GRAB_TRANSPORT = 'grab.transport.kit.KitTransport'

class KitLiveSitesTestCase(TestCase):
    pass
    #def test_dumpz_copyright(self):
        #g = Grab(transport=GRAB_TRANSPORT)
        #g.go('http://dumpz.org')
        #self.assertTrue('Grigoriy Petukhov' in g.response.body)

    #def test_dumpz_codemirror(self):
        #g = Grab(transport='grab.transport.curl.CurlTransport')
        #g.go('http://dumpz.org')
        #self.assertFalse('<div class="CodeMirror' in g.response.runtime_body)

        #g = Grab(transport=GRAB_TRANSPORT)
        #g.go('http://dumpz.org')
        ## Dumpz.org contains javascript editor CodeMirror
        ## that builds some HTML in run-time
        #self.assertTrue('<div class="CodeMirror' in g.response.runtime_body)

    #def test_show_gui(self):
        #g = Grab(transport=GRAB_TRANSPORT)
        #g.transport.kit.view.show()
        #g.go('http://dev.twitter.com/')
        #import pdb; pdb.set_trace()
        #g.transport.kit.page.mainFrame().documentElement().findAll('a')[6].toPlainText();
        #g.transport.kit.page.mainFrame().documentElement().findAll('a')[6].evaluateJavaScript('this.click()');

