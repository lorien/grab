# !/usr/bin/env python
modules = """
content
feed
http
logs
ping
russian
text
work
control
files
__init__
lxml_tools
progress
selenium_tools
user_agent
yandex
debug
google
internal
metric
pwork
structured
w3lib_encoding
encoding
html
lock
parser
rex
system
watch
""".strip().splitlines()


MODULE_CONTENT_TPL = """
from __future__ import absolute_import
from tools.%(target_module)s import * # noqa # noqa
import logging

logging.error('Module `grab.tools.%(origin_module)s` is deprecated. '
              'Use `tools.%(target_module)s` module.')

""".strip()


def generate_module_content(mod):
    if mod == 'lxml_tools':
        target_mod = 'etree'
    else:
        target_mod = mod
    return MODULE_CONTENT_TPL % {'origin_module': mod,
                                 'target_module': target_mod}


def main():
    for mod in modules:
        with open('%s.py' % mod, 'w') as out:
            out.write(generate_module_content(mod))


if __name__ == '__main__':
    main()
