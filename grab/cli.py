from __future__ import absolute_import
import os
from argparse import ArgumentParser
import logging
import sys 

from grab.util.config import build_root_config
from grab.util.py3k_support import * # noqa

logger = logging.getLogger('grab.cli')


def setup_logging(action, level, clear_handlers=False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if clear_handlers:
        for hdl in root.handlers:
            root.removeHandler(hdl)

    hdl = logging.StreamHandler()
    hdl.setLevel(level)
    root.addHandler(hdl)


def process_command_line():
    # Add current directory to python path
    cur_dir = os.path.realpath(os.getcwd())
    sys.path.insert(0, cur_dir)

    parser = ArgumentParser()
    parser.add_argument('action', type=str)
    parser.add_argument('--logging-level', default='debug')
    parser.add_argument('--lock-key')
    # parser.add_argument('--ignore-lock', action='store_true', default=False)
    parser.add_argument('--settings', type=str, default='settings')
    parser.add_argument('--env', type=str)
    parser.add_argument('--profile', action='store_true', default=False)

    args, trash = parser.parse_known_args()

    config = build_root_config()
    if config and config['GRAB_DJANGO_SETTINGS']:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
        # Turn off DEBUG to prevent memory leaks
        from django.conf import settings
        settings.DEBUG = False

    # Setup logging
    logging_level = getattr(logging, args.logging_level.upper())
    setup_logging(args.action, logging_level, clear_handlers=True)

    # Setup action handler
    action_name = args.action
    try:
        # First, try to import script from the grab package
        action_mod = __import__('grab.script.%s' % action_name, None, None,
                                ['foo'])
    except ImportError as ex:
        if (unicode(ex).startswith('No module named') and
                    action_name in unicode(ex)):
            pass
        else:
            logging.error('', exc_info=ex)
        # If grab does not provides the script
        # try to import it from the current project
        try:
            action_mod = __import__('script.%s' % action_name, None, None,
                                    ['foo'])
        except ImportError as ex:
            logging.error('', exc_info=ex)
            sys.stderr.write('Could not import %s script' % action_name)
            sys.exit(1)

    if hasattr(action_mod, 'setup_arg_parser'):
        action_mod.setup_arg_parser(parser)
    args, trash = parser.parse_known_args()

    # logger.debug('Executing %s action' % action_name)
    try:
        if args.profile:
            import cProfile
            import pyprof2calltree
            import pstats

            profile_file = 'var/%s.prof' % action_name
            profile_tree_file = 'var/%s.prof.out' % action_name

            prof = cProfile.Profile()
            prof.runctx('action_mod.main(**vars(args))',
                        globals(), locals())
            stats = pstats.Stats(prof)
            stats.strip_dirs()
            pyprof2calltree.convert(stats, profile_tree_file)
        else:
            action_mod.main(**vars(args))
    except Exception as ex:
        logging.error('Unexpected exception from action handler:', exc_info=ex)
