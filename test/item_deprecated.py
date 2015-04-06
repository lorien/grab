from unittest import TestCase
from importlib import import_module

MODULES = (
    'grab.item',
    'grab.item.decorator',
    'grab.item.error',
    'grab.item.field',
    'grab.item.item',
)

class ToolsDeprecatedTestCase(TestCase):
    def test(self):
        for path in MODULES:
            import_module(path)
