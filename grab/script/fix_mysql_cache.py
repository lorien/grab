import time

from grab.spider import Spider


def setup_arg_parser(parser):
    parser.add_argument('--user')
    parser.add_argument('--passwd')
    parser.add_argument('--database')


def main(*args, **kwargs):
    bot = Spider()
    opts = {'database': kwargs['database']}
    if kwargs.get('user'):
        opts['user'] = kwargs['user']
    if kwargs.get('passwd'):
        opts['passwd'] = kwargs['passwd']
    bot.setup_cache(backend='mysql', **opts)

    cursor = bot.cache.conn.cursor()
    cursor.execute('SELECT * FROM cache LIMIT 1')
    cols = [x[0] for x in cursor.description]
    ts = int(time.time())
    if not 'timestamp' in cols:
        print('Cache table does not have timestamp column. Adding it...')
        cursor.execute('''
            ALTER TABLE cache
            ADD COLUMN timestamp INT NOT NULL DEFAULT %s''' % ts)
