class ParsingError(Exception):
    """
    Raised when some unexpected HTML is found.
    """


def build_url():
    return 'http://formyip.com/'


def parse(g):
    """
    Parse HTML reponse from formyip.com website.
    """

    try:
        ip = g.doc.select('//strong').text().split('is ')[1]
        country = g.doc.select('//b[contains(text(), "Your Country")]')\
                   .text().split(':')[1].strip()
        return {'ip': ip, 'country': country}
    except IndexError:
        raise ParsingError('Could not parser formyip.com response')
