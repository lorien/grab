from grab import GrabSelenium

g = GrabSelenium()
g.go('http://ixbt.com')
print g.xpath_text('//title')
