from grab import Grab

g = Grab()
g.setup(body_inmemory=False, body_storage_dir='/tmp')
g.go('http://ya.ru')
print g.response.body_path
print g.response._body
