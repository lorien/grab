import grab

links = (
    'http://ya.ru',
    'http://djhvyhdhsid.com',
    'http://lenta.ru',
    'http://mail.ru',
)

g = grab.Grab(reuse_cookies = False, reuse_referer = False)
g.setup(log_dir='test/')

for link in links:
    print 'GO',link
    try:
        g.go(link)
    except grab.error.GrabError, e:
        print e
        continue
    src = g.response.unicode_body()
