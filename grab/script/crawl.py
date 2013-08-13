import logging
import os
from argparse import ArgumentParser

from grab.util.config import build_spider_config, build_global_config
from grab.util.module import load_spider_class
from grab.tools.logs import default_logging
from grab.tools.lock import assert_lock
from grab.spider.save_result import save_result

logger = logging.getLogger('grab.script.crawl')

def setup_arg_parser(parser):
    parser.add_argument('spider_name', type=str)
    parser.add_argument('-t', '--thread-number', default=None, type=int,
                        help='Number of network threads')
    parser.add_argument('--slave', action='store_true', default=False,
                        help='Enable the slave-mode')
    parser.add_argument('--network-logs', action='store_true', default=False,
                        help='Dump to console details about network requests')
    parser.add_argument('--save-result', action='store_true', default=False,
                        help='Save crawling state to database')


@save_result
def main(spider_name, thread_number=None, slave=False,
         settings='settings', network_logs=False,
         *args, **kwargs):
    default_logging(propagate_network_logger=network_logs)

    lock_key = None
    if not slave:
        lock_key = 'crawl.%s' % spider_name
    if lock_key is not None:
        lock_path = 'var/run/%s.lock' % lock_key
        logger.debug('Trying to lock file: %s' % lock_path)
        assert_lock(lock_path)

    config = build_global_config(settings)
    spider_class = load_spider_class(config, spider_name)
    spider_config = build_spider_config(spider_class, config)

    if hasattr(spider_class, 'setup_extra_args'):
        parser = ArgumentParser()
        spider_class.setup_extra_args(parser)
        extra_args, trash = parser.parse_known_args()
        spider_config['extra_args'] = vars(extra_args)

    if thread_number is None:
        thread_number = spider_config.getint('GRAB_THREAD_NUMBER')

    stat_task_object = kwargs.get('stat_task_object', None)

    bot = spider_class(
        thread_number=thread_number,
        slave=slave,
        config=spider_config,
        network_try_limit=spider_config.getint('GRAB_NETWORK_TRY_LIMIT'),
        task_try_limit=spider_config.getint('GRAB_TASK_TRY_LIMIT'),
    )
    if spider_config.get('GRAB_QUEUE'):
        bot.setup_queue(**spider_config['GRAB_QUEUE'])
    if spider_config.get('GRAB_CACHE'):
        bot.setup_cache(**spider_config['GRAB_CACHE'])
    if spider_config.get('GRAB_PROXY_LIST'):
        bot.load_proxylist(**spider_config['GRAB_PROXY_LIST'])
    if spider_config.get('GRAB_COMMAND_INTERFACES'):
        for iface_config in spider_config['GRAB_COMMAND_INTERFACES']:
            bot.controller.add_interface(**iface_config)

    # Dirty hack
    # FIXIT: REMOVE
    bot.dump_spider_stats = kwargs.get('dump_spider_stats')
    bot.stats_object = kwargs.get('stats_object')

    try:
        bot.run()
    except KeyboardInterrupt:
        pass

    stats = bot.render_stats(timing=config.get('GRAB_DISPLAY_TIMING'))

    if config.get('GRAB_DISPLAY_STATS'):
        logger.debug(stats)

    pid = os.getpid()
    logger.debug('Spider pid is %d' % pid)

    if config.get('GRAB_SAVE_FATAL_ERRORS'):
        bot.save_list('fatal', 'var/fatal-%d.txt' % pid)

    if config.get('GRAB_SAVE_TASK_ADD_ERRORS'):
        bot.save_list('task-could-not-be-added', 'var/task-add-error-%d.txt' % pid)

    if config.get('GRAB_SAVE_FINAL_STATS'):
        open('var/stats-%d.txt' % pid, 'wb').write(stats)

    return {
        'spider_stats': bot.render_stats(timing=False),
        'spider_timing': bot.render_timing(),
    }
