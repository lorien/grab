"""
Miscelanius utilities which are helpful sometime.
"""
import logging
from urlparse import urlsplit

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
