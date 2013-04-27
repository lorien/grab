# coding: utf-8
#!/usr/bin/env python
import setup_script
from grab.tools.lxml_tools import clean_html

HTML1 = """
<h1 style="font-weight: bold">Привет
<a href="http://google.com/">google</a>
<div width="100">100div</div>
"""

HTML2 = HTML1.decode('utf-8')
HTML3 = HTML2.encode('cp1251')

print clean_html(HTML1)
print clean_html(HTML2)
print clean_html(HTML3, encoding='cp1251')
