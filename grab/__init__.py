from __future__ import absolute_import

from weblib.logs import default_logging  # noqa

from grab.base import Grab  # noqa
from grab.error import (  # noqa
    DataNotFound,
    GrabError,
    GrabMisuseError,
    GrabNetworkError,
    GrabTimeoutError,
)
from grab.upload import UploadContent, UploadFile  # noqa

__version__ = "1.0.0"
VERSION_NUMERIC = tuple(map(int, __version__.split(".")))
