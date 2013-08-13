# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from datetime import datetime
import logging
from ..base import Grab
#from .. import error
from ..response import Response
#from ..tools.http import encode_cookies, urlencode, normalize_unicode,\
                         #normalize_http_values
#from ..tools.user_agent import random_user_agent
from ..error import GrabNetworkError

class GrabMockNotFoundError(GrabNetworkError):
    """
    Raised when MOCK_REGISTRY does not have required URL.
    """

logger = logging.getLogger('grab.transport.mock')

MOCK_REGISTRY = {
}

class MockTransport(object):
    """
    Grab transport layer using pycurl.
    """

    #def __init__(self):
        #self.curl = pycurl.Curl()

    def reset(self):
        self.request_head = ''
        self.request_body = ''
        self.request_log = ''

    def process_config(self, grab):
        """
        Setup curl instance with values from ``self.config``.
        """

        self.request_url = grab.config['url']

    def request(self):
        pass

    def prepare_response(self, grab):
        response = Response()
        
        try:
            response.body = MOCK_REGISTRY[self.request_url]['body']
        except KeyError:
            raise GrabMockNotFoundError(
                'Mock registry does not have information about '\
                'following URL: %s' % self.request_url)

        now_str = datetime.now().strftime('%a, %d %B %Y %H:%M:%S')
        response.head = '\r\n'.join((
            'Accept-Ranges:bytes',
            'Content-Length:%d' % len(response.body),
            'Content-Type:text/plain',
            'Date:%s GMT' % now_str,
            'Last-Modified:%s GMT' % now_str,
            'Vary:Accept-Encoding',
        ))

        response.code = 200
        response.total_time = 0
        response.name_lookup_time = 0
        response.connect_time = 0
        response.url = self.request_url
        response.parse()
        response.cookies = self.extract_cookies()

        return response

    def extract_cookies(self):
        return {}


class GrabMock(Grab):
    def __init__(self, response_body=None, transport='grab.transport.curl.CurlTransport',
                 **kwargs):
        super(GrabMock, self).__init__(response_body=response_body,
                                       transport='grab.transport.mock.MockTransport',
                                       **kwargs)
