import logging


def default_logging(grab_log='/tmp/grab.log', level=logging.DEBUG, mode='a',
                    propagate_network_logger=False,
                    network_log='/tmp/grab.network.log'):
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


#LOGGING_BUFFER = defaultdict(list)
#GLOBAL = {'key': None}

#class MemoryHandler(logging.Handler):
    #def emit(self, record):
        #LOGGING_BUFFER[GLOBAL['key']].append(self.format(record))


#logger = logging.getLogger('calculate')
#logger.addHandler(MemoryHandler())


#def save_logging(func):
    #def inner(*args, **kwargs):
        #key = str(time.time()) + str(id({}))
        #GLOBAL['key'] = key 
        #try:
            #result = func(*args, **kwargs)
            #result['logs'] = copy(LOGGING_BUFFER[key])
        #finally:
            #if key in LOGGING_BUFFER:
                #del LOGGING_BUFFER[key]
        #return result
    #return inner
