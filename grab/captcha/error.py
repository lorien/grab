__all__ = ('CaptchaError', 'CaptchaServiceError', 'SolutionNotReady',
           'ServiceTooBusy', 'BalanceTooLow')


class CaptchaError(Exception):
    pass


class CaptchaServiceError(CaptchaError):
    pass


class SolutionNotReady(CaptchaServiceError):
    pass


class ServiceTooBusy(CaptchaServiceError):
    pass


class BalanceTooLow(CaptchaServiceError):
    pass
