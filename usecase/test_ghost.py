import setup_script

from grab import Grab

g = Grab(transport='ghost.GhostTransport')
g.go('http://ya.ru/')
print g.xpath_text('//title')
