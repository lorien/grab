from hashlib import sha1


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
