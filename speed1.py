import cStringIO
import StringIO
import time

COUNT = 10000

def main():
    print 'List'
    start = time.time()
    items = []
    for x in xrange(COUNT):
        items.append(str(time.time()))
    result = ''.join(items)
    print '%.04f' % (time.time() - start)

    print 'cStringIO'
    start = time.time()
    items = cStringIO.StringIO()
    for x in xrange(COUNT):
        items.write(str(time.time()))
    result = items.getvalue()
    print '%.04f' % (time.time() - start)

    print 'StringIO'
    start = time.time()
    items = StringIO.StringIO()
    for x in xrange(COUNT):
        items.write(str(time.time()))
    result = items.getvalue()
    print '%.04f' % (time.time() - start)

    print 'String'
    start = time.time()
    items = ''
    for x in xrange(COUNT):
        items += str(time.time())
    result = items
    print '%.04f' % (time.time() - start)


main()
