from unittest import TestCase

from grab.util.module import import_string, ImportStringError


class UtilModuleTestCase(TestCase):
    def test_import_string(self):
        mod = import_string('tests.case.util_module')
        self.assertTrue(hasattr(mod, 'UtilModuleTestCase'))

    def test_import_string_error(self):
        self.assertRaises(ImportStringError, import_string,
                          'tests.case.zzzzzzzzzzzz')
