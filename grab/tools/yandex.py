import urllib

from .encoding import smart_str

class CaptchaError(Exception):
    """
    Raised when yandex shows captcha.
    """


def is_banned(grab):
    return grab.xpath_exists('//input[@class="b-captcha__input"]')


def build_search_url(query, page=1, per_page=None, lang='en', filter=True,
                     region=213, **kwargs):
    """
    Build yandex search url with specified query and pagination options.

    :param per_page: 10, 20, 30, 50, 100

    213 region is Moscow
    """

    query = smart_str(query)
    url = 'http://yandex.ru/yandsearch?text=%s&lr=%s' % (
        urllib.quote(query), region)
    if kwargs:
        url += '&' + urlencode(kwargs)
    return url
