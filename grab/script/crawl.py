import logging
import os
from argparse import ArgumentParser

from grab.util.config import build_spider_config, build_root_config
from grab.util.module import load_spider_class
from grab.tools.logs import default_logging
from grab.tools.lock import assert_lock
from grab.spider.save_result import save_result
from grab.tools.files import clear_directory
from grab.tools.encoding import make_str

logger = logging.getLogger('grab.script.crawl')


def setup_arg_parser(parser):
    parser.add_argument('spider_name', type=str)
    parser.add_argument('-t', '--thread-number', default=None, type=int,
                        help='Number of network threads')
    parser.add_argument('--slave', action='store_true', default=False,
                        help='Enable the slave-mode')
    parser.add_argument('-n', '--network-logs', action='store_true', default=False,
                        help='Dump to console details about network requests')
    parser.add_argument('--save-result', action='store_true', default=False,
                        help='Save crawling state to database')
    parser.add_argument('--disable-proxy', action='store_true', default=False,
                        help='Disable proxy servers')
    parser.add_argument('--ignore-lock', action='store_true', default=False)
    parser.add_argument('--disable-report', action='store_true', default=False)
    parser.add_argument('--settings-module', type=str, default='settings')


#def get_spider_setting(spider_config, key, deprecated_key=None, key_type=None,
                       #default=None): 
    #"""
    #Get setting's value from the config that could be either in
    #deprecated or in actual format.
    #"""
    ## try actual format
    #try:
        #value = spider_config[key]
    #except TypeError:
        #raise
        ##import pdb; pdb.set_trace()
    #except KeyError:
        #if deprecated_key is not None:
            #try:
                #value = spider_config[deprecated_key]
            #except KeyError:
                #value = default
        #else:
            #value = default
    #if key_type is None:
        #return value
    #elif key_type == 'int':
        #return int(value)


def get_lock_key(spider_name, lock_key=None, ignore_lock=False, slave=False, **kwargs):
    # --ignore-lock has highest precedence
    if ignore_lock:
        return None

    # If --lock-key is specified explicitly use it
    if lock_key is not None:
        return lock_key

    # Do not lock --slave spiders
    if slave:
        return None

    # As fallback, if no information has been given about locking
    # generate lock key from the spider name and use it
    lock_key = 'crawl.%s' % spider_name
    return lock_key


@save_result
def main(spider_name, thread_number=None, slave=False,
         settings_module='settings', network_logs=False,
         disable_proxy=False, ignore_lock=False, 
         disable_report=False,
         *args, **kwargs):
    default_logging(propagate_network_logger=network_logs)

    root_config = build_root_config(settings_module)
    spider_class = load_spider_class(root_config, spider_name)
    spider_config = build_spider_config(spider_class, root_config)

    spider_args = None
    if hasattr(spider_class, 'setup_arg_parser'):
        parser = ArgumentParser()
        spider_class.setup_arg_parser(parser)
        opts, trash = parser.parse_known_args()
        spider_args = vars(opts)

    if thread_number is None:
        thread_number = \
            int(spider_config.get('thread_number',
                                  deprecated_key='GRAB_THREAD_NUMBER'))

    stat_task_object = kwargs.get('stat_task_object', None)

    bot = spider_class(
        thread_number=thread_number,
        slave=slave,
        config=spider_config,
        network_try_limit=int(spider_config.get(
            'network_try_limit', deprecated_key='GRAB_NETWORK_TRY_LIMIT')),
        task_try_limit=int(spider_config.get(
            'task_try_limit', deprecated_key='GRAB_TASK_TRY_LIMIT')),
        args=spider_args,
    )
    opt_queue = spider_config.get('queue', deprecated_key='GRAB_QUEUE')
    if opt_queue:
        bot.setup_queue(**opt_queue)

    opt_cache = spider_config.get('cache', deprecated_key='GRAB_CACHE')
    if opt_cache:
        bot.setup_cache(**opt_cache)

    opt_proxy_list = spider_config.get(
        'proxy_list', deprecated_key='GRAB_PROXY_LIST')
    if opt_proxy_list:
        if disable_proxy:
            logger.debug('Proxy servers disabled via command line')
        else:
            bot.load_proxylist(**opt_proxy_list)

    opt_ifaces = spider_config.get(
        'command_interfaces', deprecated_key='GRAB_COMMAND_INTERFACES')
    if opt_ifaces:
        for iface_config in opt_ifaces:
            bot.controller.add_interface(**iface_config)

    # Dirty hack
    # FIXIT: REMOVE
    bot.dump_spider_stats = kwargs.get('dump_spider_stats')
    bot.stats_object = kwargs.get('stats_object')

    try:
        bot.run()
    except KeyboardInterrupt:
        pass

    stats = bot.render_stats(
        timing=spider_config.get('display_timing',
                                 deprecated_key='GRAB_DISPLAY_TIMING'))
    stats_with_time = bot.render_stats(timing=True)

    if spider_config.get('display_stats', deprecated_key='GRAB_DISPLAY_STATS'):
        logger.debug(stats)

    pid = os.getpid()
    logger.debug('Spider pid is %d' % pid)

    if not disable_report:
        if spider_config.get('save_report', deprecated_key='GRAB_SAVE_REPORT'):
            for subdir in (str(pid), 'last'):
                dir_ = 'var/%s' % subdir
                if not os.path.exists(dir_):
                    os.mkdir(dir_)
                else:
                    clear_directory(dir_)
                for key, lst in bot.items.items():
                    fname_key = key.replace('-', '_')
                    bot.save_list(key, '%s/%s.txt' % (dir_, fname_key))
                with open('%s/report.txt' % dir_, 'wb') as out:
                    out.write(make_str(stats_with_time))

    return {
        'spider_stats': bot.render_stats(timing=False),
        'spider_timing': bot.render_timing(),
    }
