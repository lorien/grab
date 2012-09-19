from grab import Grab

g = Grab()
g.setup(post='foo', method='put')
g.go('http://h.wrttn.me/put')
print g.request_headers
print g.response.body
