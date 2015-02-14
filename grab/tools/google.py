# coding: utf-8
"""
Google parser.

Generic search algorithm:

    With some query:
        For page in 1...9999:
            Build url for given query and page
            Request the url
            If captcha found:
                Solve captcha or change proxy or do something else
            If last page found:
                Stop parsing


Module contents:

* CaptchaFound
* ParsingError
* build_search_url
* parse_index_size
* is_last_page
* parse_search_results

"""
try:
    from urllib import quote, unquote_plus
except ImportError:
    from urllib.parse import quote, unquote_plus
import logging
import re
import base64

from grab.tools.html import decode_entities
from grab.tools.lxml_tools import get_node_text, drop_node, render_html
from grab.tools.http import urlencode
from grab.tools.encoding import smart_str
from grab.tools.text import find_number


class CaptchaFound(Exception):
    """
    Raised when google fucks you with captcha.
    """


class CaptchaError(CaptchaFound):
    """
    TODO: display deprecation warning
    """


class AccessDenied(Exception):
    """
    Raised when HTTP 403 code is received.
    """


class ParsingError(Exception):
    """
    Raised when some unexpected HTML is found.
    """


def build_search_url(query, page=None, per_page=None, lang=None,
                     filter=None, **kwargs):
    """
    Build google search url with specified query and pagination options.

    :param per_page: 10, 20, 30, 50, 100
    kwargs:
        tbs=qdr:h
        tbs=qdr:d
        tbs=qdr:w
        tbs=qdr:m
        tbs=qdr:y
    """

    if per_page is None:
        per_page = 10
    if page is None:
        page = 1
    if lang is None:
        lang = 'en'
    if filter is None:
        filter = True
    start = per_page * (page - 1)

    if not 'hl' in kwargs:
        kwargs['hl'] = lang
    if not 'num' in kwargs:
        kwargs['num'] = per_page
    if not 'start' in kwargs:
        kwargs['start'] = start
    if not 'filter' in kwargs:
        if not filter:
            kwargs['filter'] = '0'


    url = 'http://google.com/search?q=%s' % quote(smart_str(query))
    if kwargs:
        url += '&' + urlencode(kwargs)
    return url


def parse_index_size(grab):
    """
    Extract number of results from grab instance which
    has received google search results.
    """

    text = None
    if grab.search(u'did not match any documents'):
        return 0
    if len(grab.css_list('#resultStats')):
        text = grab.css_text('#resultStats')
    if len(grab.xpath_list('//div[@id="subform_ctrl"]/div[2]')):
        text = grab.xpath_text('//div[@id="subform_ctrl"]/div[2]')
    if text is None:
        logging.error('Unknown google page format')
        return 0
    text = text.replace(',', '').replace('.', '')
    if 'about' in text:
        number = find_number(text.split('about')[1])
        return int(number)
    elif 'of' in text:
        number = find_number(text.split('of')[1])
        return int(number)
    else:
        number = find_number(text)
        return int(number)


#def search(query, grab=None, limit=None, per_page=None):

    #if not grab:
        #grab = Grab()
    #stop = False
    #count = 0

    #grab.clear_cookies()
    #if grab.proxylist:
        #grab.change_proxy()

    #for page in xrange(1, 9999):
        #if stop:
            #break
        #url = build_search_url(query, page, per_page=per_page)
        #index_size = None
        #grab = google_request(url, grab=grab)

        #count = 0
        #for item in parse_search_results(grab):
            #yield item # {url, title, index_size}
            #count += 1

        #if not count:
            #stop = True

        #if is_last_page(grab):
            #logging.debug('Last page found')
            #stop = True

        #if limit is not None and count >= limit:
            #logging.debug('Limit %d reached' % limit)
            #stop = True

        #grab.sleep(3, 5)


def is_last_page(grab):
    """
    Detect if the fetched page is last page of search results.
    """

    # <td class="b" style="text-align:left"><a href="/search?q=punbb&amp;num=100&amp;hl=ru&amp;prmd=ivns&amp;ei=67DBTs3TJMfpOfrhkcsB&amp;start=100&amp;sa=N" style="text-align:left"><span class="csb ch" style="background-position:-96px 0;width:71px"></span><span style="display:block;margin-left:53px">{NEXT MESSAGE}</span></a></td>

    try:
        #next_link_text = grab.xpath_list('//span[contains(@class, "csb ") and '\
                                         #'contains(@class, " ch")]/..')[-1]\
                             #.text_content().strip()
        next_link = grab.xpath_one('//a[@id="pnnext"]')
    except IndexError:
        logging.debug('No results found')
        return True
    else:
        return False
        #return not len(next_link_text)



def parse_search_results(grab, parse_index_size=False, strict_query=False):
    """
    Parse google search results page content.
    """

    #elif grab.search(u'please type the characters below'):
    if grab.response.code == 403:
        raise AccessDenied('Access denied (HTTP 403)')
    elif grab.search(u'src="/sorry/image'):

        # Captcha!!!
        raise CaptchaFound('Captcha found')

    elif grab.css_exists('#ires'):
        if strict_query and \
                grab.search(u'Нет результатов для') or \
                grab.search(u'No results found for'):
            pass
            logging.debug('Query modified')
        else:
            if len(grab.css_list('#ires h3')):

                # Something was found
                if parse_index_size:
                    index_size = parse_index_size(grab)
                else:
                    index_size = None

                # Yield found results
                results = []

                for elem in grab.xpath_list('//*[h3[@class="r"]/a]'):
                    title_elem = elem.xpath('h3/a')[0]

                    # url
                    url = title_elem.get('href')
                    if url.startswith('/url?'):
                        url = url.split('?q=')[1].split('&')[0]
                        url = unquote_plus(url)

                    # title
                    title = get_node_text(title_elem)

                    # snippet
                    # Google could offer two type of snippet format: simple and extended
                    # It depends on user agent
                    # For <IE8, Opera, <FF3 you probably get simple format
                    try:
                        snippet_node = elem.xpath('div[@class="s"]')[0]
                    except IndexError as ex:
                        # Probably it is video or some other result
                        # Such result type is not supported yet
                        continue

                    try:
                        subnode = snippet_node.xpath('span[@class="st"]')[0]
                        snippet = get_node_text(subnode, smart=False)
                        extended_result = True
                    except IndexError:
                        drop_node(snippet_node, 'div')
                        drop_node(snippet_node, 'span[@class="f"]')
                        snippet = get_node_text(snippet_node, smart=False)
                        extended_result = False

                    # filetype
                    try:
                        filetype = elem.xpath('.//span[contains(@class, "xsm")]'\
                                              '/text()')[0].lower().strip('[]')
                    except IndexError:
                        filetype = None

                    #if 'File Format':
                    if url:
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'filetype': filetype,
                            'index_size': index_size,
                            'extended': extended_result,
                        })
                return results
            else:
                pass
                #return []
    elif grab.css_exists('#res'):
        # Could be search results here?
        # or just message "nothing was found"?
        pass
    else:
        raise ParsingError('Could not identify google page format')
