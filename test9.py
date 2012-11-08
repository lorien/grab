from grab import Grab
import logging

logging.basicConfig(level=logging.DEBUG)
g = Grab()
g.setup(log_dir='var/log', debug=True)
g.go('http://yandex.ru')
