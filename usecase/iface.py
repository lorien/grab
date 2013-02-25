import setup_script

from grab import Grab

g = Grab()
g.setup(url='http://ya.ru/')
g.setup(interface='tun0')
g.request()
print g.doc.select('//title').text()

g.setup(interface='foo')
try:
    g.request()
except Exception, ex:
    print ex
else:
    print g.doc.select('//title').text()

g.setup(interface='192.168.170.18')
g.request()
print g.doc.select('//title').text()
