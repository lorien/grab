from unittest import TestCase
from importlib import import_module

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
    def test(self):
        for mod_name in MODULES:
            path = 'grab.tools.%s' % mod_name
            import_module(path)
