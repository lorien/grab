from hashlib import md5
import time
import os
import mimetypes

from weblib.encoding import make_str


class BaseUploadObject(object):
    __slots__ = ()

    def find_content_type(self, filename):
        ctype, _ = mimetypes.guess_type(filename)
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
