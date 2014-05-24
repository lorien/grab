try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from grab import Grab
from grab.tools.encoding import smart_str

name = 'clck.ru'

def get_url(url):
    g = Grab()
    g.go('http://clck.ru/--?url=%s' % quote(smart_str(url)))
    return g.response.body
