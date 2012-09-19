from grab import Grab

g = Grab()
g.setup(post='foo', method='put', debug=True)
g.go('http://h.wrttn.me/put')
print g.request_headers
print g.response.body
