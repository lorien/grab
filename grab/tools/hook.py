from importlib import import_module
import logging


class CustomImporter(object):
    virtual_name = 'grab.tools'

    def find_module(self, name, path=None):
        if name.find(self.virtual_name) == 0:
            name = name.split('.')

            if name[-1] == 'lxml_tools':
                name[-1] = 'etree'

            if len(name) == 3:
                self.name = '.%s' % (name[-1])
            else:
                self.name = ''

            logging.error('Module `grab.tools%s` is deprecated. '
                          'Use `weblib%s` module.' % (self.name, self.name))
            return self
        return None

    def load_module(self, name):
        return import_module(self.name, 'weblib')
