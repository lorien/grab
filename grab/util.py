"""
Miscelanius utilities which are helpful sometime.
"""
import logging

def unique_file(path):
    """
    Drop non-unique lines in the file.
    Return number of unique lines.
    """

    lines = set()
    count = 0
    for line in open(path):
        lines.add(line)
        count += 1
    logging.debug('Read %d lines from %s, unique: %d' % (count, path,
                                                         len(lines)))
    open(path, 'w').write(''.join(lines))
    return len(lines)
