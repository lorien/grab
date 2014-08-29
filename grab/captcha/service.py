import logging

from grab.util.module import import_string
from grab.captcha.const import BACKEND_ALIAS

__all__ = ('CaptchaService',)
logger = logging.getLogger('grab.captcha')


class CaptchaService(object):
    """
    This class implements API to communicate with
    remote captcha solving service.
    """

    def __init__(self, backend, **kwargs):
        if backend in BACKEND_ALIAS:
            backend_path = BACKEND_ALIAS[backend]
        else:
            backend_path = backend
        self.backend = import_string(backend_path)()
        self.backend.setup(**kwargs)

    def submit_captcha(self, data, **kwargs):
        g = self.backend.get_submit_captcha_request(data, **kwargs)
        g.request()
        return self.backend.parse_submit_captcha_response(g.response)

    def check_solution(self, captcha_id):
        """
        Raises:
        * SolutionNotReady
        * ServiceTooBusy
        """

        g = self.backend.get_check_solution_request(captcha_id)
        g.request()
        return self.backend.parse_check_solution_response(g.response)
