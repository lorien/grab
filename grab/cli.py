import os
from argparse import ArgumentParser
import logging
from grab.tools.lock import assert_lock
import time
import traceback
from datetime import datetime, timedelta
import sys 
from grab.tools.logs import default_logging
from grab import Grab
import sys 
#import setup_django

logger = logging.getLogger('grab.cli')

def setup_logging(action, level):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    #for hdl in root.handlers:
    #    root.removeHandler(hdl)

    hdl = logging.StreamHandler()
    hdl.setLevel(level)
    #hdl.setFormatter(logging.Formatter('%(message)s'))
    #hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    root.addHandler(hdl)

    # debug log
    fname = 'var/log/%s.debug.log' % action
    hdl = logging.FileHandler(fname, 'a')
    hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    hdl.setLevel(logging.DEBUG)
    root.addHandler(hdl)

    # error log
    fname = 'var/log/%s.error.log' % action
    hdl = logging.FileHandler(fname, 'a')
    hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    hdl.setLevel(logging.ERROR)
    root.addHandler(hdl)

    # common error log
    fname = 'var/log/error.log'
    hdl = logging.FileHandler(fname, 'a')
    hdl.setFormatter(logging.Formatter('%(asctime)s: [%(name)s] %(message)s'))
    hdl.setLevel(logging.ERROR)
    root.addHandler(hdl)

    #root.setLevel(logging.DEBUG)
    #default_logging(level=level)


def process_command_line():
    # Add current directory to python path
    cur_dir = os.path.realpath(os.getcwd())
    sys.path.insert(0, cur_dir)

    parser = ArgumentParser()
    parser.add_argument('action', type=str)
    parser.add_argument('positional_args', nargs='*')
    parser.add_argument('-t', '--thread-number', help='Number of network threads',
                        default=1, type=int)
    parser.add_argument('--logging-level', default='debug')
    parser.add_argument('--slave', action='store_true', default=False)
    parser.add_argument('--lock-key')
    parser.add_argument('--ignore-lock', action='store_true', default=False)

    args, trash = parser.parse_known_args()

    # Setup logging
    logging_level = getattr(logging, args.logging_level.upper())
    if args.positional_args:
        command_key = '_'.join([args.action] + args.positional_args)
    else:
        command_key = args.action
    # TODO: enable logs
    #setup_logging(command_key, logging_level)

    # Setup action handler
    action_name = args.action
    try:
        # First, try to import script from the grab package
        action_mod = __import__('grab.script.%s' % action_name, None, None, ['foo'])
    except ImportError:
        # If grab does not provides the script
        # try to import it from the current project
        try:
            action_mod = __import__('script.%s' % action_name, None, None, ['foo'])
        except ImportError:
            sys.stderr.write('Could not import %s script' % action_name)
            sys.exit(1)

    if hasattr(action_mod, 'setup_arg_parser'):
        action_mod.setup_arg_parser(parser)
    args = parser.parse_args()

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

    logger.debug('Execution %s action' % action_name)
    try:
        action_mod.main(*args.positional_args, **vars(args))
    except Exception, ex:
        logging.error('Unexpected exception from action handler:', exc_info=ex)
