import os
from argparse import ArgumentParser
import logging
from grab.tools.lock import assert_lock
from grab.tools.logs import default_logging
import sys 

from grab.util.config import build_global_config

from grab.util.py3k_support import *

logger = logging.getLogger('grab.cli')

def activate_env(env_path):
    activate_script = os.path.join(env_path, 'bin/activate_this.py')
    # py3 hack
    if PY3K:
        exec(compile(open(activate_script).read(), activate_script, 'exec'),
             dict(__file__=activate_script))
    else:
        execfile(activate_script, dict(__file__=activate_script))


def setup_logging(action, level, clear_handlers=False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if clear_handlers:
        for hdl in root.handlers:
            root.removeHandler(hdl)

    hdl = logging.StreamHandler()
    hdl.setLevel(level)
    #hdl.setFormatter(logging.Formatter('%(message)s'))
    #hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    root.addHandler(hdl)

    # debug log
    #fname = 'var/log/%s.debug.log' % action
    #hdl = logging.FileHandler(fname, 'a')
    #hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    #hdl.setLevel(logging.DEBUG)
    #root.addHandler(hdl)

    # error log
    #fname = 'var/log/%s.error.log' % action
    #hdl = logging.FileHandler(fname, 'a')
    #hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    #hdl.setLevel(logging.ERROR)
    #root.addHandler(hdl)

    # common error log
    #fname = 'var/log/error.log'
    #hdl = logging.FileHandler(fname, 'a')
    #hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    #hdl.setLevel(logging.ERROR)
    #root.addHandler(hdl)

    #root.setLevel(logging.DEBUG)
    #default_logging(level=level)


def process_env_option():
    parser = ArgumentParser()
    parser.add_argument('--env')
    args, trash = parser.parse_known_args()
    if args.env:
        activate_env(args.env)


def process_command_line():
    # Add current directory to python path
    cur_dir = os.path.realpath(os.getcwd())
    sys.path.insert(0, cur_dir)

    process_env_option()

    parser = ArgumentParser()
    parser.add_argument('action', type=str)
    parser.add_argument('--logging-level', default='debug')
    parser.add_argument('--lock-key')
    parser.add_argument('--ignore-lock', action='store_true', default=False)
    parser.add_argument('--settings', type=str, default='settings')
    parser.add_argument('--env', type=str)

    args, trash = parser.parse_known_args()

    config = build_global_config()
    if config and config['GRAB_DJANGO_SETTINGS']:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
        # Turn off DEBUG to prevent memory leaks
        from django.conf import settings
        settings.DEBUG = False

    # Setup logging
    logging_level = getattr(logging, args.logging_level.upper())
    #if args.positional_args:
        #command_key = '_'.join([args.action] + args.positional_args)
    #else:
        #command_key = args.action
    # TODO: enable logs
    setup_logging(args.action, logging_level, clear_handlers=True)

    # Setup action handler
    action_name = args.action
    try:
        # First, try to import script from the grab package
        action_mod = __import__('grab.script.%s' % action_name, None, None, ['foo'])
    except ImportError as ex:
        if (unicode(ex).startswith('No module named') and
            action_name in unicode(ex)):
            pass
        else:
            logging.error('', exc_info=ex)
        # If grab does not provides the script
        # try to import it from the current project
        try:
            action_mod = __import__('script.%s' % action_name, None, None, ['foo'])
        except ImportError as ex:
            logging.error('', exc_info=ex)
            sys.stderr.write('Could not import %s script' % action_name)
            sys.exit(1)

    if hasattr(action_mod, 'setup_arg_parser'):
        action_mod.setup_arg_parser(parser)
    args, trash = parser.parse_known_args()

    # TODO: enable lock-file processing
    #lock_key = None
    #if not args.slave:
        #if not args.ignore_lock:
            #if not args.lock_key:
                #if hasattr(action_mod, 'setup_lock_key'):
                    #lock_key = action_mod.setup_lock_key(action_name, args)
                #else:
                    #lock_key = command_key
            #else:
                #lock_key = args.lock_key
    #if lock_key is not None:
        #lock_path = 'var/run/%s.lock' % lock_key
        #print 'Trying to lock file: %s' % lock_path
        #assert_lock(lock_path)

    logger.debug('Executing %s action' % action_name)
    try:
        action_mod.main(**vars(args))
    except Exception as ex:
        logging.error('Unexpected exception from action handler:', exc_info=ex)
