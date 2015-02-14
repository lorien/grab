from tempfile import mkstemp
from base64 import b64encode
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from grab import Grab
from grab.captcha.backend.base import CaptchaBackend
from grab.captcha.error import (CaptchaServiceError, ServiceTooBusy,
                                BalanceTooLow, SolutionNotReady)


class AntigateBackend(CaptchaBackend):
    def setup(self, api_key):
        self.api_key = api_key

    def get_submit_captcha_request(self, data, **kwargs):
        g = Grab()
        post = {
            'key': self.api_key,
            'method': 'base64',
            'body': b64encode(data),
        }
        post.update(kwargs)
        g.setup(post=post)
        g.setup(url='http://antigate.com/in.php')
        return g

    def parse_submit_captcha_response(self, res):
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
        
    def get_check_solution_request(self, captcha_id):
        params = {'key': self.api_key, 'action': 'get', 'id': captcha_id}
        url = 'http://antigate.com/res.php?%s' % urlencode(params)
        g = Grab()
        g.setup(url=url)
        return g

    def parse_check_solution_response(self, res):
        if res.code == 200:
            if res.body.startswith('OK|'):
                return res.body.split('|', 1)[1]
            elif res.body == 'CAPCHA_NOT_READY':
                raise SolutionNotReady('Solution not ready')
            else:
                raise CaptchaServiceError(res.body)
        else:
            raise CaptchaServiceError('Returned HTTP code: %d' % res.code)
