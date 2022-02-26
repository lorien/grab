import logging
import sys
from contextlib import contextmanager
from io import TextIOBase


def setup_logger(
    name: str,
    filename: str,
    filemode: str,
    propagate: bool = True,
    level: int = logging.DEBUG,
):
    logger = logging.getLogger(name)
    logger.propagate = propagate
    hdl = logging.FileHandler(filename, filemode)
    logger.addHandler(hdl)
    logger.setLevel(level)


def default_logging(
    grab_log=None,  # '/tmp/grab.log',
    network_log=None,  # '/tmp/grab.network.log',
    level=logging.DEBUG,
    mode="a",
    propagate_network_logger=False,
):
    """
    Customize logging output to display all log messages
    except grab network logs.

    Redirect grab network logs into file.
    """

    logging.basicConfig(level=level)
    if network_log:
        setup_logger(
            name="grab.network",
            filename=network_log,
            filemode=mode,
            propagate=propagate_network_logger,
            level=level,
        )
    if grab_log:
        setup_logger(
            name="grab",
            filename=grab_log,
            filemode=mode,
            propagate=True,
            level=level,
        )


class PycurlSigintHandler(TextIOBase):
    # TextIOBase to avoid errors in py36: https://bugs.python.org/issue29130
    def __init__(self, *args, **kwargs):
        super(PycurlSigintHandler, self).__init__(*args, **kwargs)
        self.orig_stderr = None
        self.buf = []

    @contextmanager
    def record(self):
        # NB: it is not thread-safe
        self.buf = []
        self.orig_stderr = sys.stderr
        try:
            sys.stderr = self
            yield
        finally:
            sys.stderr = self.orig_stderr

    def write(self, data):
        self.orig_stderr.write(data)
        self.buf.append(data)

    def get_output(self):
        return "".join(self.buf)

    @contextmanager
    def handle_sigint(self):
        with self.record():
            try:
                yield
            except Exception as ex:  # pylint: disable=broad-except
                if "KeyboardInterrupt" in self.get_output():
                    raise KeyboardInterrupt from ex
                else:
                    raise
            else:
                if "KeyboardInterrupt" in self.get_output():
                    raise KeyboardInterrupt
