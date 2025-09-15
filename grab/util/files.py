import os
import shutil
from hashlib import sha1

from six.moves.urllib.parse import urlsplit


def hashed_path_details(url, ext="jpg", base_dir=None):
    _hash = sha1(url).hexdigest()
    a, b, tail = _hash[:2], _hash[2:4], _hash[4:]
    directory = "%s/%s" % (a, b)
    if base_dir is not None:
        directory = "%s/%s" % (base_dir, directory)
    if ext is not None:
        filename = "%s.%s" % (tail, ext)
    else:
        filename = tail
    full_path = "%s/%s" % (directory, filename)
    return {
        "directory": directory,
        "filename": filename,
        "full_path": full_path,
    }


def hashed_path(url, ext="jpg", base_dir=None):
    return hashed_path_details(url, ext=ext, base_dir=base_dir)["full_path"]


def clear_directory(path):
    """
    Delete recursively all directories and files in
    specified directory.
    """

    for root, dirs, files in os.walk(path):
        for fname in files:
            os.unlink(os.path.join(root, fname))
        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))
