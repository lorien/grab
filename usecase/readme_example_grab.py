from grab import Grab

g = Grab()
g.go('https://github.com/login')
g.set_input('login', 'lorien')
g.set_input('password', '***')
g.submit()

for elem in g.doc.select('//ul[@id="repo_listing"]/li/a'):
    print '%s: %s' % (elem.text(), elem.attr('href'))
