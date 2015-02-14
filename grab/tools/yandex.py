# coding: utf-8
try:
    from urllib import quote #, unquote_plus
except ImportError:
    from urllib.parse import quote #, unquote_plus
from grab.tools.lxml_tools import get_node_text
import logging

from grab.tools.encoding import smart_str


class CaptchaError(Exception):
    """
    Raised when yandex shows captcha.
    """


def is_banned(grab):
    if grab.xpath_exists('//input[@class="b-captcha__input"]'):
        return True
    if grab.xpath_text('//title') == '403':
        return True
    return False


def build_search_url(query, page=1, per_page=None, lang='en', filter=True,
                     region=213, **kwargs):
    """
    Build yandex search url with specified query and pagination options.

    :param per_page: 10, 20, 30, 50, 100

    213 region is Moscow
    """

    query = smart_str(query)
    url = 'http://yandex.ru/yandsearch?text=%s&lr=%s' % (
        quote(query), region)
    if kwargs:
        url += '&' + urlencode(kwargs)
    url += '&p=%d' % (page - 1)
    return url


def is_last_page(grab):
    """
    Detect if the fetched page is last page of search results.
    """

    try:
        next_link = grab.xpath_one('//a[contains(@class, "b-pager__next")]')
    except IndexError:
        logging.debug('No results found')
        return True
    else:
        return False


def parse_search_results(grab, parse_index_size=False, strict_query=False):
    """
    Parse yandex search results page content.
    """

    if is_banned(grab):
        raise CaptchaError('Captcha found')

    elif grab.xpath_exists('//div[contains(@class, "b-error")]'):
        err_msg = grab.xpath_text('//div[contains(@class, "b-error")]')
        logging.debug('Found error message: %s' % err_msg)
        return []
    elif grab.xpath_exists('//ol[contains(@class, "b-serp-list")]'):
        # TODO:
        #if (strict_query and (
            #grab.search(u'Нет результатов для') or grab.search(u'No results found for'))):
            #pass
            #logging.debug('Query modified')
        results = []
        # TODO: parse_index_size
        # Yield found results
        results = []

        page_num = int(grab.xpath_text('//b[contains(@class, "b-pager__current")]'))

        for elem in grab.xpath_list('//li[contains(@class, "b-serp-item")]'):
            try:
                try:
                    title_elem = elem.xpath('.//h2/a')[0]
                    snippet = get_node_text(
                        elem.xpath('.//div[contains(@class, "b-serp-item__text")]')[0])
                except IndexError:
                    # this is video item or something like that
                    pass
                else:
                    item = {
                        'page': page_num,
                    }

                    # url
                    item['url'] = title_elem.get('href')
                    #if url.startswith('/url?'):
                        #url = url.split('?q=')[1].split('&')[0]
                        #url = unquote_plus(url)

                    item['position'] = int(elem.xpath(
                        './/h2/b[contains(@class, "b-serp-item__number")]/text()')[0])

                    # title
                    item['title'] = get_node_text(title_elem)

                    item['snippet'] = snippet

                    results.append(item)
            except Exception as ex:
                logging.error('', exc_info=ex)

        return results
    else:
        print('parsing error')
        raise ParsingError('Could not identify yandex page format')
