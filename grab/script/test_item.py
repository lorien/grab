from grab import Grab


def setup_arg_parser(parser):
    parser.add_argument('item_path')
    parser.add_argument('--all', action='store_true', default=False)


def main(item_path, **kwargs):
    mod_path, cls_name = item_path.rsplit('.', 1)
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
        except Exception as ex:
            print('Fatal exception:')
            print(ex)
        else:
            print('URL: %s' % url)
            for count, item in enumerate(cls.find(cls.extract_document_data(g),
                                                  url=g.response.url)):
                print('%s #%d' % (cls.__name__, count))
                print(item._render())
                print('----------')
