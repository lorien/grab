#!/usr/bin/python3
from grab import Grab

g = Grab()
g.go('http://ya.ru/')
print(g.response.code)
