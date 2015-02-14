class InvalidMonthName(Exception):
    pass


def parse_int(val):
    if val is None:
        return None
    else:
        return int(val)


def parse_en_month(val):
    names = (None, u'january', u'february', u'march', u'april',
             u'may', u'june', u'july', u'august',
             u'september', u'october', u'november', u'december')
    try:
        return names.index(val.lower())
    except ValueError:
        raise InvalidMonthName(u'Invalid month name: %s' % val)
