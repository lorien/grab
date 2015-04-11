from __future__ import absolute_import
from hashlib import md5
import time
from weblib.encoding import make_str
import os
import mimetypes


class BaseUploadObject(object):
    __slots__ = ()

    def find_content_type(self, filename):
        ctype, encoding = mimetypes.guess_type(filename)
        if ctype is None:
            return 'application/octet-stream'
        else:
            return ctype


class UploadContent(BaseUploadObject):
    __slots__ = ('content', 'filename', 'content_type')

    def __init__(self, content, filename=None, content_type=None):
        self.content = content
        if filename is None:
            self.filename = self.get_random_filename()
        else:
            self.filename = filename
        if content_type is None:
            self.content_type = self.find_content_type(self.filename)
        else:
            self.content_type = content_type

    def get_random_filename(self):
        return md5(make_str(str(time.time()))).hexdigest()[:10]


class UploadFile(BaseUploadObject):
    __slots__ = ('path', 'filename', 'content_type')

    def __init__(self, path, filename=None, content_type=None):
        self.path = path
        if filename is None:
            self.filename = os.path.split(path)[1]
        else:
            self.filename = filename
        if content_type is None:
            self.content_type = self.find_content_type(self.filename)
        else:
            self.content_type = content_type


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
