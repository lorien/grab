# coding: utf-8
from unittest import TestCase
from lxml.html import fromstring

from grab.tools.content import find_content_blocks

class GrabSimpleTestCase(TestCase):
    def test_find_content_blocks(self):
        porno = u'порно ' * 100
        redis = u'редис ' * 100
        html = ('<div>%s</div><p>%s' % (porno, redis))
        tree = fromstring(html)
        blocks = list(find_content_blocks(tree, min_length=100))
        #print '>>>'
        #print blocks[0]
        #print len(blocks[0])
        #print '<<<'
        #print ')))'
        #print porno.strip()
        #print len(porno.strip())
        #print '((('
        self.assertEqual(blocks[0], porno)
        self.assertEqual(blocks[1], redis)
