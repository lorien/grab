"""
This module provides function to fetch network documents with multicurl
in asynchronious mode.
"""
import pycurl
import logging
from grab import Grab

def multi_fetch(generator, thread_number, **kwargs):
    """
    Download documents asynchroniously.

    Arguments:
    * generator - generator which yield urls
    * thread_number - number of concurrent download-streams
    """
    
    # Apply iterator interface
    # for sequence which is not iterator already
    generator = iter(generator)

    m = pycurl.CurlMulti()
    m.handles = []

    # Create curl instances
    for x in xrange(thread_number):
        g = Grab(**kwargs)
        g.curl.grab = g
        m.handles.append(g.curl)

    freelist = m.handles[:]
    num_processed = 0
    no_tasks = False

    while True:
        # If tasks and free curl instances
        while not no_tasks and freelist:
            try:
                url = generator.next()
            except StopIteration:
                no_tasks = True
                break
            else:
                curl = freelist.pop()
                # Set up curl instance via Grab interface
                curl.grab.setup(url=url)
                curl.grab.prepare_request()
                curl._meta = {'url': url}
                # Add configured curl instance to multi-curl processor
                m.add_handle(curl)

        while True:
            status, active_objects = m.perform()
            if status != pycurl.E_CALL_MULTI_PERFORM:
                break

        while True:
            queued_messages, ok_list, fail_list = m.info_read()

            for curl in ok_list:
                logging.debug('OK: %s' % curl._meta['url'])
                curl.grab.process_request_result()
                m.remove_handle(curl)
                freelist.append(curl)
                yield {'ok': True, 'grab': curl.grab.clone(),
                       'url': curl._meta['url']}

            for curl, ecode, emsg in fail_list:
                logging.debug('FAIL [%s]: %s' % (emsg, curl._meta['url']))
                m.remove_handle(curl)
                freelist.append(curl)
                yield {'ok': False, 'grab': curl.grab.clone(),
                        'url': curl._meta['url'], 'ecode': ecode,
                        'emsg': emsg}

            num_processed += (len(ok_list) + len(fail_list))
            if not queued_messages:
                break

        if no_tasks and len(freelist) == thread_number:
            break

        m.select(0.5)
