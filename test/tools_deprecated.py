from unittest import TestCase
from importlib import import_module
from grab.tools.hook import CustomImporter

MODULES = """
content
feed
http
logs
ping
russian
text
work
control
files
__init__
lxml_tools
progress
selenium_tools
user_agent
yandex
debug
google
internal
metric
pwork
structured
w3lib_encoding
encoding
html
lock
parser
rex
system
watch
""".strip().splitlines()

class ToolsDeprecatedTestCase(TestCase):
    def setUp(self):
        self.hook = CustomImporter()

    def test_import_traditional_way(self):
        for mod_name in MODULES:
            path = 'grab.tools.%s' % mod_name
            import_module(path)

    def test_hook(self):
        for mod_name in MODULES:
            path = 'grab.tools.%s' % mod_name
            self.hook.find_module(path)
            self.hook.load_module(path)

    def test_hook2(self):
        self.assertIsInstance(self.hook.find_module('grab.tools.yandex'),
                              CustomImporter)
        self.assertEqual(self.hook.find_module('grab.spider'),
                         None)

        self.hook.find_module('grab.tools.lxml_tools')
        self.assertEqual(self.hook.name, '.etree')

        self.hook.find_module('grab.tools.module')
        self.assertRaises(ImportError, self.hook.load_module,
                          'grab.tools.module')

