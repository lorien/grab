from grab import Grab
import logging

logging.basicConfig(level=logging.DEBUG, debug_post=True)

g = Grab()
g.go("http://google.ru/", method='post', post='')
print g.response.code
