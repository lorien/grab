from importlib import import_module
import logging
import sys

from grab.util.warning import warn


class CustomImporter(object):
    """
    Class that hooks grab.tools imports and then redirect it to weblib package
    """
    virtual_name = 'grab.tools'

    def find_module(self, name, path=None):
        """
        This method is called by Python if this class is on sys.path. This
        method will be called every time an import
        statement is detected (or __import__ is called), before
        Python's built-in package/module-finding code kicks in.
        """
        if name.find(self.virtual_name) == 0:
            name = name.split('.')

            if name[-1] == 'lxml_tools':
                name[-1] = 'etree'

            if len(name) == 3:
                self.name = '.' + '.'.join(name[2:])
            else:
                self.name = ''

            return self
        return None

    def load_module(self, name):
        """
        This method is called by Python if CustomImporter.find_module
         does not return None.
        """
        try:
            module = import_module(self.name, 'weblib')
            sys.modules[name] = module
            warn('Module `grab.tools%s` is deprecated. '
                 'Use `weblib%s` module.' % (self.name, self.name))
        except:
            raise ImportError(name)

        return module
