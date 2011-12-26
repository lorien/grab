import logging

def default_logging(grab_log='/tmp/grab.log'):
    """
    Customize logging output to display all log messages
    except grab network logs.

    Redirect grab network logs into file.
    """

    logging.basicConfig(level=logging.DEBUG)
    glog = logging.getLogger('grab')
    glog.propagate = False
    if grab_log:
        hdl = logging.FileHandler(grab_log, 'w')
        glog.addHandler(hdl)
