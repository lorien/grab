import logging
import sys
from contextlib import contextmanager


def default_logging(grab_log=None,#'/tmp/grab.log',
                    network_log=None,#'/tmp/grab.network.log',
                    level=logging.DEBUG, mode='a',
                    propagate_network_logger=False,
                    ):
    """
    Customize logging output to display all log messages
    except grab network logs.

    Redirect grab network logs into file.
    """

    logging.basicConfig(level=level)

    network_logger = logging.getLogger('grab.network')
    network_logger.propagate = propagate_network_logger
    if network_log:
        hdl = logging.FileHandler(network_log, mode)
        network_logger.addHandler(hdl)
        network_logger.setLevel(level)

    grab_logger = logging.getLogger('grab')
    if grab_log:
        hdl = logging.FileHandler(grab_log, mode)
        grab_logger.addHandler(hdl)
        grab_logger.setLevel(level)


class StderrProxy(object):
    def __init__(self):
        if not hasattr(sys, '_orig_stderr'):
            sys._orig_stderr = sys.stderr
        self.buf = []

    @contextmanager
    def record(self):
        self.buf = []
        try:
            sys.stderr = self
            yield
        finally:
            sys.stderr = sys._orig_stderr

    def write(self, data):
        sys._orig_stderr.write(data)
        self.buf.append(data)

    def get_output(self):
        return ''.join(self.buf)
        #return 'def body_processor(self, chunk):\nKeyboardInterrupt'
