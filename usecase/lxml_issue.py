# coding: utf-8
import setup_script
from grab import Grab

g = Grab()
g.go('http://alvogen.ru/')
g.xpath('//a')
