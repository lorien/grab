from grab import Grab
from tempfile import mkstemp
from base64 import b64encode
import urllib

from ..error import (CaptchaServiceError, ServiceTooBusy, BalanceTooLow,
                     SolutionNotReady)
#import urllib2
#import urllib
#import logging
#import time
#from StringIO import StringIO

#from .contrib.poster.encode import multipart_encode, MultipartParam
#from .contrib.poster.streaminghttp import register_openers
#from .error import CaptchaError

#register_openers()
#logger = logging.getLogger('grab.tools.captcha.antigate')

class AntigateBackend(object):
    def __init__(self, api_key):
        self.setup(api_key)

    def setup(self, api_key):
        self.api_key = api_key

    def submit_captcha(self, data, **kwargs):
        g = Grab()

        post={
            'key': self.api_key,
            'method': 'base64',
            'body': b64encode(data),
        }
        post.update(kwargs)
        g.setup(post=post)
        g.setup(url='http://antigate.com/in.php')
        res = g.request()
        if res.code == 200:
            if res.body.startswith('OK|'):
                return res.body.split('|', 1)[1]
            elif res.body == 'ERROR_NO_SLOT_AVAILABLE':
                raise ServiceTooBusy('Service too busy')
            elif res.body == 'ERROR_ZERO_BALANCE':
                raise BalanceTooLow('Balance too low')
            else:
                raise CaptchaServiceError(res.body)
        else:
            raise CaptchaServiceError('Returned HTTP code: %d' % res.code)
        
    def check_solution(self, captcha_id):
        params = {'key': self.api_key, 'action': 'get', 'id': captcha_id}
        url = 'http://antigate.com/res.php?%s' % urllib.urlencode(params)
        g = Grab()
        res = g.go(url)
        if res.code == 200:
            if res.body.startswith('OK|'):
                return res.body.split('|', 1)[1]
            elif res.body == 'CAPCHA_NOT_READY':
                raise SolutionNotReady('Solution not ready')
            else:
                raise CaptchaServiceError(res.body)
        else:
            raise CaptchaServiceError('Returned HTTP code: %d' % res.code)


#def send_captcha(key, fobj):
    #items = []
    #items.append(MultipartParam(name='key', value=key))
    #items.append(MultipartParam(name='method', value='post'))
    #items.append(MultipartParam(name='file', filename='captcha.jpg',
                                #fileobj=fobj))

    #data, headers = multipart_encode(items)
    #req = urllib2.Request('http://antigate.com/in.php', data, headers)
    #res = urllib2.urlopen(req)
    #if res.code == 200:
        #chunks = res.read().split('|')
        #if len(chunks) == 2:
            #return int(chunks[1])
        #else:
            #msg = chunks[0]
            #raise CaptchaError(msg)
    #else:
        #msg = '%s %s' % (res.code, res.msg)
        #raise CaptchaError(msg)
    #print res.info()
    #return res.read()

#def get_solution(key, captcha_id):
    ##logger.debug('Getting solution for captcha %s' % captcha_id)
    #params = {'key': key, 'action': 'get', 'id': captcha_id}
    #url = 'http://antigate.com/res.php?%s' % urllib.urlencode(params)
    #data = urllib.urlopen(url).read()
    #chunks = data.split('|')
    #if len(chunks) == 2:
        #return chunks[1]
    #else:
        #msg = chunks[0]
        #raise CaptchaError(msg)


#def solve_captcha(key, data):
    #if key is None:
        #raise Exception('antigate key could not None')

    #fobj = StringIO(data)

    #captcha_id = None
    #for x in xrange(30):
        #try:
            #captcha_id = send_captcha(key, fobj)
        #except CaptchaError as ex:
            #if ex.args[0] == 'ERROR_NO_SLOT_AVAILABLE':
                #logger.debug('No antigate slot available')
                #time.sleep(1)
            #else:
                #raise
        #else:
            #break
            
    #if captcha_id is None:
        #raise CaptchaError('No antigate slot available')

    #logger.debug('Getting solution for captcha#%d' % captcha_id)
    #for x in xrange(20):
        #try:
            #return get_solution(key, captcha_id)
        #except CaptchaError, ex:
            #if ex.args[0] == 'CAPCHA_NOT_READY':
                ##logger.debug('Waiting for captcha solution')
                #time.sleep(3)
            #else:
                #raise

    #raise CaptchaError('No antigate slot available')
