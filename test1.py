from grab import Grab
import logging

logging.basicConfig(level=logging.DEBUG, debug_post=True)

g = Grab()
g.setup(headers={'Accept-Encoding': 'gzip,deflate,sdch', 'Accept-Charset': 'windows-1251,utf-8;q=0.7,*;q=0.3', 'Accept':'*/*', 'Origin':'http://www.pluralsight-training.net', 'Connection':'keep-alive', 'Accept-Language':'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4'})
g.go('http://yandex.ru/')
print g.request_headers
