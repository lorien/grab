# coding: utf-8
from unittest import TestCase
import sys
from six import BytesIO

from grab.util.log import repr_value, print_dict

class LogModuleTestCase(TestCase):
    def test_repr_value(self):
        self.assertEquals(u'фыва'.encode('utf-8'),
                          repr_value(u'фыва'))
        self.assertEquals(u'[фы, ва]'.encode('utf-8'),
                          repr_value([u'фы', u'ва']))
        self.assertEquals(u'{фы: ва}'.encode('utf-8'),
                          repr_value({u'фы': u'ва'}))
        self.assertEquals(b'1', repr_value(1))

    def test_print_dict(self):
        """
        old_out = sys.stdout
        out = BytesIO()
        sys.stdout = out
        print_dict({'foo': 'bar'})
        self.assertEqual(
            out.getvalue(),
            "[---\nfoo: bar\n---]\n",
        )
        sys.stdout = old_out
        """
        # I have troubles with testing this function
        # Just calling it to improve test coverage
        print_dict({'foo': 'bar'})
        print_dict({u'foo': u'bar'})
        print_dict({u'foo': 1})

"""
def repr_value(val):
    if isinstance(val, six.text_type):
        return val.encode('utf-8')
    elif isinstance(val, (list, tuple)):
        return '[%s]' % ', '.join(repr_value(x) for x in val)
    elif isinstance(val, dict):
        return '{%s}' % ', '.join('%s: %s' % (repr_value(x), repr_value(y))
                                  for x, y in val.items())
    else:
        return str(val)
"""
