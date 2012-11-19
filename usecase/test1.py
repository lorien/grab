import setup_script

import grab

urls = ['http://karta-moskvy.ru']

g = grab.Grab(hammer_mode=True)
#g.setup(strip_xml_declaration=True)

for url in urls:
    g.go(url)
    print g.response.unicode_body()
    #for a in g.xpath_list('//a'):
        #h = a.get('href','')
