"""
This module contains `print_dict` function that is useful
to dump content of dictionary in human acceptable representation.
"""
import six
import logging


def repr_value(val):
    if isinstance(val, six.text_type):
        return val.encode('utf-8')
    elif isinstance(val, (list, tuple)):
        return b'[' + b', '.join(repr_value(x) for x in val) + b']'
    elif isinstance(val, dict):
        return b'{' + b', '.join((repr_value(x) + b': ' + repr_value(y))
                               for x, y in val.items()) + b'}'
    else:
        return six.b(str(val))


def print_dict(dic):
    print(b'[---')
    for key, val in sorted(dic.items(), key=lambda x: x[0]):
        print(repr_value(key) + b': ' + repr_value(val))
    print(b'---]')



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
