import setup_script

from grab import Grab

g = Grab()
g.go('http://ya.ru')
print g.xpath('//title')
