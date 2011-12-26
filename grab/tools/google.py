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

* CaptchaError
* ParsingError
* build_search_url
* parse_index_size
* is_last_page
* parse_search_results

"""
import urllib
import logging
import re
import base64

from grab.tools.html import decode_entities
from grab.tools.lxml import get_node_text

ANONYMIZER_ARG = re.compile(r'q=([^&"]+)')

class CaptchaError(Exception):
    """
    Raised when google fucks you with captcha.
    """


class ParsingError(Exception):
    """
    Raised when some unexpected HTML is found.
    """


class AnonymizerNetworkError(Exception):
    """
    Raised in case of standard anonymizer error.
    """


def build_search_url(query, page=1, per_page=None, lang='en', filter=True):
    """
    Build google search url with specified query and pagination options.
    """

    if per_page is None:
        per_page = 10
    if isinstance(query, unicode):
        query = query.encode('utf-8')
    start = per_page * (page - 1)
    url = 'http://google.com/search?hl=%s&q=%s&start=%s' % (
        lang, urllib.quote(query), start)
    if per_page != 10:
        url += '&num=%d' % per_page
    if not filter:
        url += '&filter=0'
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
        number = grab.find_number(text.split('about')[1])
        return int(number)
    elif 'of' in text:
        number = grab.find_number(text.split('of')[1])
        return int(number)
    else:
        number = grab.find_number(text)
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
        next_link_text = grab.xpath_list('//span[contains(@class, "csb ") and '\
                                         'contains(@class, " ch")]/..')[-1]\
                             .text_content().strip()
    except IndexError:
        logging.debug('No results found')
        return True
    else:
        return not len(next_link_text)



def parse_search_results(grab, parse_index_size=False, anonymizer=False):
    """
    Parse google search results page content.
    """

    #elif grab.search(u'please type the characters below'):
    if grab.search(u'src="/sorry/image'):

        # Captcha!!!
        raise CaptchaError('Captcha found')

    elif anonymizer and grab.search(u'URL Error (0)'):

        # Common anonymizer error
        raise AnonymizerNetworkError('URL Error (0)')

    elif grab.css_exists('#ires'):
        if len(grab.css_list('#ires h3')):

            # Something was found
            if parse_index_size:
                index_size = parse_index_size(grab)
            else:
                index_size = None

            # Yield found results
            for elem in grab.css_list('h3.r a'):
                url = elem.get('href')
                if anonymizer:
                    match = ANONYMIZER_ARG.search(url)
                    if match:
                        token = urllib.unquote(match.group(1))
                        url = decode_entities(base64.b64decode(token))
                    else:
                        url = None
                        logging.error('Could not parse url encoded by anonymizer')

                if url:
                    yield {'url': url, 'title': get_node_text(elem),
                           'index_size': index_size}
        else:
            pass
            #return []
    else:
        raise ParsingError('Could not identify google page format')
