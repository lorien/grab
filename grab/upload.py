from __future__ import annotations

import mimetypes
import os
import time
from hashlib import md5


class BaseUploadItem:
    __slots__ = ()

    def find_content_type(self, filename: str) -> str:
        ctype, _ = mimetypes.guess_type(filename)
        if ctype is None:
            return "application/octet-stream"
        return ctype


class UploadContent(BaseUploadItem):
    __slots__ = ("content", "filename", "content_type")

    def __init__(
        self,
        content: bytes,
        filename: None | str = None,
        content_type: None | str = None,
    ) -> None:
        self.content = content
        if filename is None:
            self.filename = self.get_random_filename()
        else:
            self.filename = filename
        if content_type is None:
            self.content_type = self.find_content_type(self.filename)
        else:
            self.content_type = content_type

    def get_random_filename(self) -> str:
        return md5(str(time.time()).encode()).hexdigest()[:10]


class UploadFile(BaseUploadItem):
    __slots__ = ("path", "filename", "content_type")

    def __init__(
        self,
        path: str,
        filename: None | str = None,
        content_type: None | str = None,
    ) -> None:
        self.path = path
        if filename is None:
            self.filename = os.path.split(path)[1]
        else:
            self.filename = filename
        if content_type is None:
            self.content_type = self.find_content_type(self.filename)
        else:
            self.content_type = content_type
