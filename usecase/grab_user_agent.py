import setup_script
from grab import Grab

g = Grab()
g.setup(debug=True)
g.go('http://ya.ru/')
print g.request_headers['User-Agent']

g.setup(user_agent=None)
g.go('http://ya.ru/')
print g.request_headers['User-Agent']
