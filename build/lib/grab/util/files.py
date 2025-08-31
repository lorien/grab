from __future__ import annotations

from hashlib import sha1


def hashed_path_details(
    url: str, ext: None | str = None, base_dir: None | str = None
) -> dict[str, str]:
    _hash = sha1(url.encode()).hexdigest()
    part1, part2, tail = _hash[:2], _hash[2:4], _hash[4:]
    directory = "%s/%s" % (part1, part2)
    if base_dir is not None:
        directory = "%s/%s" % (base_dir, directory)
    filename = "%s.%s" % (tail, ext) if (ext is not None) else tail
    full_path = "%s/%s" % (directory, filename)
    return {
        "directory": directory,
        "filename": filename,
        "full_path": full_path,
    }


def hashed_path(url: str, ext: None | str = None, base_dir: None | str = None) -> str:
    return hashed_path_details(url, ext=ext, base_dir=base_dir)["full_path"]
