"""
tinyurl.com
"""
from grab import Grab

name = 'tinyurl.com'

def get_url(url):
    g = Grab()
    g.go('http://tinyurl.com/')
    g.assert_substring(u'Welcome to TinyURL')
    g.set_input('url', url)
    g.submit()
    g.assert_substring(u'TinyURL was created')
    return g.xpath_text('//td/blockquote[2]/b')
