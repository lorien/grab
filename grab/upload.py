from __future__ import absolute_import
from hashlib import md5
import time
from tools.encoding import make_str


class UploadContent(object):
    def __init__(self, content, filename=None):
        if filename is None:
            self.filename = self.get_random_filename()
            
        else:
            self.filename = filename
        self.content = content

    def get_random_filename(self):
        return md5(make_str(str(time.time()))).hexdigest()[:10]


class UploadFile(object):
    def __init__(self, path):
        self.path = path


"""
class UploadContent(str):
    def __new__(cls, value):
        obj = str.__new__(cls, 'xxx')
        obj.raw_value = value
        return obj

    def field_tuple(self):
        # TODO: move to transport extension
        import pycurl
        return pycurl.FORM_CONTENTS, self.raw_value


class UploadFile(str):
    def __new__(cls, path):
        obj = str.__new__(cls, 'xxx')
        obj.path = path
        return obj

    def field_tuple(self):
        # move to transport extension
        import pycurl
        return pycurl.FORM_FILE, self.path
"""
