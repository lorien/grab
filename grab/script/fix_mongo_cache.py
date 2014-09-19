import time

from grab.spider import Spider


def setup_arg_parser(parser):
    parser.add_argument('--database')


def main(*args, **kwargs):
    bot = Spider()
    opts = {'database': kwargs['database']}
    bot.setup_cache(backend='mongo', **opts)

    ts = int(time.time())
    count = 0
    for item in bot.cache.db.cache.find({'timestamp': {'$exists': False}},
                                        timeout=False):
        bot.cache.db.cache.update({'_id': item['_id']},
                                  {'$set': {'timestamp': ts}})
        count += 1
    print('Records updated: %d' % count)
