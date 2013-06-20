import logging

from ..util.module import import_string
from .const import BACKEND_ALIAS

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
        self.backend = import_string(backend_path)(**kwargs)

    def submit_captcha(self, data):
        return self.backend.submit_captcha(data)

    def check_solution(self, reqid): 
        """
        Raises:
        * SolutionNotReady
        * ServiceTooBusy
        """

        return self.backend.check_solution(reqid)
