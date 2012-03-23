import urllib
import re

urls = """
http://genofond.binec.ru/default2.aspx?p=98
http://genofond.binec.ru/default2.aspx?s=0&p=69
http://genofond.binec.ru/default2.aspx?s=0&p=70
http://genofond.binec.ru/default2.aspx?s=0&p=71
http://genofond.binec.ru/default2.aspx?s=0&p=72
http://genofond.binec.ru/default2.aspx?s=0&p=73
http://genofond.binec.ru/default2.aspx?s=0&p=74
http://genofond.binec.ru/default2.aspx?s=0&p=75
http://genofond.binec.ru/default2.aspx?s=0&p=76
http://genofond.binec.ru/default2.aspx?s=0&p=77
http://genofond.binec.ru/default2.aspx?s=0&p=78
http://genofond.binec.ru/default2.aspx?s=0&p=79
http://genofond.binec.ru/default2.aspx?s=0&p=80
http://genofond.binec.ru/default2.aspx?s=0&p=81
http://genofond.binec.ru/default2.aspx?s=0&p=82
http://genofond.binec.ru/default2.aspx?s=0&p=83
http://genofond.binec.ru/default2.aspx?s=0&p=84
http://genofond.binec.ru/default2.aspx?s=0&p=85
http://genofond.binec.ru/default2.aspx?s=0&p=88
http://genofond.binec.ru/default2.aspx?s=0&p=89
http://genofond.binec.ru/default2.aspx?s=0&p=90
http://genofond.binec.ru/default2.aspx?s=0&p=91
http://genofond.binec.ru/default2.aspx?s=0&p=92
http://genofond.binec.ru/default2.aspx?s=0&p=93
http://genofond.binec.ru/default2.aspx?s=0&p=94
http://genofond.binec.ru/default2.aspx?s=0&p=95
http://genofond.binec.ru/default2.aspx?s=0&p=96
http://genofond.binec.ru/default2.aspx?s=0&p=97
"""

urls = [x.strip() for x in urls.strip().splitlines()]

re_lname = re.compile(r'<FONT face=Calibri color=#000000 size=3>([^\d][^<]+)</FONT>')
outfile = file('ru_lname.txt', 'w')

for url in urls:
    print url
    data = urllib.urlopen(url).read().decode('cp1251')

    items = []
    for lname in re_lname.findall(data):
        lname = lname.lower().capitalize()
        outfile.write(lname.encode('utf-8') + '\n')
        print lname
