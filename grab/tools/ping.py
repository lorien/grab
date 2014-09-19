from grab import Grab
import logging
import os

from grab.tools import html
from grab.tools.pwork import make_work
from grab.tools.encoding import smart_str
from grab.util.py3k_support import *

PING_XML = """<?xml version="1.0"?>
<methodCall>
 	<methodName>weblogUpdates.ping</methodName>
 	<params>
        <param><value>%(name)s</value></param>
        <param><value>%(url)s</value></param>
 	</params>
</methodCall>
"""

SERVER_LIST = """
http://audiorpc.weblogs.com/RPC2
http://blogsearch.google.com.ua/ping/RPC2
http://blogsearch.google.com/ping/RPC2
http://blogsearch.google.ru/ping/RPC2
http://ping.blogs.yandex.ru/RPC2
http://ping.myblog.jp/
http://rpc.weblogs.com/RPC2
http://xping.pubsub.com/ping
""".strip().splitlines()


def ping(name, url, grab, thread_number=10):
    """
    Do XMLRPC ping of given site.
    """
    
    name = smart_str(name)
    url = smart_str(url)

    def worker(rpc_url):
        post = PING_XML % {
            'url': html.escape(url),
            'name': html.escape(name),
        }
        ok = False
        try:
            grab.go(rpc_url, post=post)
        except Exception as ex:
            logging.error(unicode(ex))
        else:
            if not '<boolean>0' in grab.response.body:
                logging.error('%s : FAIL' % rpc_url)
                logging.error(grab.response.body[:1000])
            else:
                ok = True
        return rpc_url, ok

    results = []
    for rpc_url, ok in make_work(worker, SERVER_LIST, thread_number):
        results.append((rpc_url, ok))
    return results


if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    g = Grab(timeout=15)
    g.setup_proxylist('/web/proxy.txt', 'http', auto_change=True) 
    items = ping('seobeginner.ru', 'http://feeds2.feedburner.com/seobeginner',
                 g, thread_number=30)
    print('RESULT:')
    for rpc, ok in items:
        print(rpc, ok)
