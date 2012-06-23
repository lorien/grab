from grab import Grab
import logging

logging.basicConfig(level=logging.DEBUG)

g = Grab()
g.setup()
#del g.config['common_headers']['Keep-Alive']
g.go('http://yandex.ru')

print g.request_headers
print 'K-A:', g.request_headers['Keep-Alive']
