from grab import Grab

g = Grab()

g.setup(cookiefile = '/tmp/cookies.txt')
g.setup(cookies={'test': 'test'})
g.go('http://ya.ru/')
print g.response.cookies
