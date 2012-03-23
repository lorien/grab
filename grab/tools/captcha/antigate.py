import urllib2
import urllib
import logging
import time
from StringIO import StringIO

from .contrib.poster.encode import multipart_encode, MultipartParam
from .contrib.poster.streaminghttp import register_openers
from .error import CaptchaError

register_openers()
logger = logging.getLogger('tools.captcha.antigate')

def send_captcha(key, fobj):
    logger.debug('Sending captcha')
    items = []
    items.append(MultipartParam(name='key', value=key))
    items.append(MultipartParam(name='method', value='post'))
    items.append(MultipartParam(name='file', filename='captcha.jpg',
                                fileobj=fobj))

    data, headers = multipart_encode(items)
    req = urllib2.Request('http://antigate.com/in.php', data, headers)
    res = urllib2.urlopen(req)
    if res.code == 200:
        chunks = res.read().split('|')
        if len(chunks) == 2:
            return int(chunks[1])
        else:
            msg = chunks[0]
            logger.debug(msg)
            raise CaptchaError(msg)
    else:
        msg = '%s %s' % (res.code, res.msg)
        logger.debug(msg)
        raise CaptchaError(msg)
    print res.info()
    return res.read()

def get_solution(key, captcha_id):
    logger.debug('Fetching solution for captcha %s' % captcha_id)
    params = {'key': key, 'action': 'get', 'id': captcha_id}
    url = 'http://antigate.com/res.php?%s' % urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    chunks = data.split('|')
    if len(chunks) == 2:
        return chunks[1]
    else:
        msg = chunks[0]
        raise CaptchaError(msg)


def solve_captcha(key, data):
    fobj = StringIO(data)
    while True:
        try:
            captcha_id = send_captcha(key, fobj)
        except CaptchaError, ex:
            if ex.args[0] == 'ERROR_NO_SLOT_AVAILABLE':
                logger.debug('No slot available')
                pass
            else:
                raise
        else:
            break

    while True:
        try:
            return get_solution(key, captcha_id)
        except CaptchaError, ex:
            if ex.args[0] == 'CAPCHA_NOT_READY':
                logger.debug('Waiting for captcha solution')
                time.sleep(3)
            else:
                logger.debug(ex)
                raise


def test_logging():
    logger.debug('asdf')
