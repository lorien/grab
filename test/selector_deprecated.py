from unittest import TestCase
from importlib import import_module
from lxml.html import fromstring
from six import StringIO
import mock

from grab.selector import XpathSelector

MODULES = (
    'grab.selector',
    'grab.selector.selector',
)

class ToolsDeprecatedTestCase(TestCase):
    def test(self):
        for path in MODULES:
            import_module(path)

    def test_xpath_selector(self):
        tree = fromstring('<div>test</div>')
        out = StringIO()
        with mock.patch('sys.stderr', out):
            XpathSelector(tree)
        self.assertTrue(
            'using XpathSelector from deprecated' in out.getvalue())
