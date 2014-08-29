"""
Miscellaneous utilities which are helpful sometime.
"""
import logging
try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit
from hashlib import sha1
import os
import shutil


def unique_file(path):
    """
    Drop non-unique lines in the file.
    Return number of unique lines.
    """

    lines = set()
    count = 0
    with open(path) as inf:
        for line in inf:
            lines.add(line)
            count += 1
    logging.debug('Read %d lines from %s, unique: %d' % (count, path,
                                                         len(lines)))
    with open(path, 'w') as out:
        out.write(''.join(lines))
    return len(lines)


def unique_host(path):
    """
    Filter out urls with duplicated hostnames.
    """

    hosts = set()
    lines = []
    count = 0
    with open(path) as inf:
        for line in inf:
            host = urlsplit(line).netloc
            if not host in hosts:
                lines.append(line)
                hosts.add(host)
            count += 1
    logging.debug('Read %d lines from %s, unique hosts: %d' % (count, path,
                                                               len(lines)))
    with open(path, 'w') as out:
        out.write(''.join(lines))
    return len(lines)


def hashed_path_details(url, ext='jpg', base_dir=None):
    _hash = sha1(url).hexdigest()
    a, b, tail = _hash[:2], _hash[2:4], _hash[4:]
    directory = '%s/%s' % (a, b)
    if base_dir is not None:
        directory = '%s/%s' % (base_dir, directory)
    if ext is not None:
        filename = '%s.%s' % (tail, ext)
    else:
        filename = tail
    full_path = '%s/%s' % (directory, filename)
    return {'directory': directory,
            'filename': filename,
            'full_path': full_path,
            }


def hashed_path(url, ext='jpg', base_dir=None):
    dtl = hashed_path_details(url, ext=ext, base_dir=base_dir)
    return dtl['full_path']


# Alias for back-ward compatibility
def hash_path(*args, **kwargs):
    logging.debug('This function name is deprecated. '
                  'Please use hashed_path function')
    return hashed_path(*args, **kwargs)


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


# Bad name, not clear logic
#def smart_copy_file(filename, dst_root):
    #dir_path, fname = os.path.split(filename)
    #dst_dir = os.path.join(dst_root, dir_path)
    #if not os.path.exists(dst_dir):
        #os.makedirs(dst_dir)
    #import pdb; pdb.set_trace()
    #shutil.copy(filename, dst_dir)
