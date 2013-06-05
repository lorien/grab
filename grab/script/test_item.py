from grab import Grab

def setup_arg_parser(parser):
    parser.add_argument('--all', action='store_true', default=False)


def main(*args, **kwargs):
    mod_path, cls_name = args[0].rsplit('.', 1)
    mod = __import__(mod_path, None, None, ['foo'])
    cls = getattr(mod, cls_name)

    if kwargs.get('all'):
        urls = cls.Meta.example_urls
    else:
        urls = [cls.Meta.example_url]

    g = Grab()
    for url in urls:
        try:
            g.go(url)
        except Exception, ex: 
            print 'Fatal exception:'
            print ex
        else:
            print 'URL: %s' % url 
            for count, item in enumerate(cls.find(g.doc, url=g.response.url)):
                print '%s #%d' % (cls.__name__, count)
                print item._render()
                print '----------'
