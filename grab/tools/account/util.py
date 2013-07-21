import os.path
try:
    from string import letters
except ImportError:
    from string import ascii_letters as letters
from string import digits, ascii_lowercase, ascii_uppercase
from random import choice, randint
from datetime import date
from functools import reduce

from grab.util.py3k_support import *

SAFE_CHARS = letters + digits
S_CHARS = 'bcdfghjklmnpqrstvwxz'
G_CHARS = 'aeiouy'
EMAIL_SERVERS = ['gmail.com', 'yahoo.com']

FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')
CACHE = {}

def load_items(name):
    if not name in CACHE:
        path = os.path.join(FILES_DIR, name)
        items = [x.strip().decode('utf-8') for x in open(path) if x.strip()]
        CACHE[name] = items
    return CACHE[name]


def random_password(min_length=8, max_length=10):
    """
    Make random password.

    Ensures that password has at least one digit, upper case letter and
    lower case letter.
    """

    chars = ''.join(map(choice, (ascii_lowercase, ascii_uppercase, digits)))
    length = list(range(randint(min_length, max_length) - len(chars)))
    return reduce(lambda a, b: a + choice(SAFE_CHARS), length, chars)


def random_login(min_length=8, max_length=8):
    """
    Make random login.
    """

    length = randint(min_length, max_length)
    chars = []
    for x in xrange(0, length, 2):
       chars.extend((choice(G_CHARS), choice(S_CHARS)))
    return ''.join(chars[:length])


def random_birthday(start_year=1960, end_year=1990):
    """
    Make random birth date.
    """

    date_obj = date(randint(start_year, end_year), randint(1, 12), randint(1, 28))
    return {
        'day': str(date_obj.day),
        'month': str(date_obj.month),
        'year': str(date_obj.year),
        'date': date_obj,
    }


def random_email(login=None):
    """
    Make random email.
    """

    if not login:
        login = random_login()
    return '%s@%s' % (login, choice(EMAIL_SERVERS))


def random_fname(lang='en'):
    """
    Return random first name.
    """

    return choice(load_items('%s_fname.txt' % lang))


def random_lname(lang='en'):
    """
    Return random last name.
    """

    return choice(load_items('%s_lname.txt' % lang))


def random_city(lang='en'):
    """
    Return random city.
    """

    return choice(load_items('%s_city.txt' % lang))


def random_icq():
    """
    Make random ICQ number.
    """

    return  str(randint(100000000, 999999999))


def random_phone():
    """
    Return random phone
    """

    return '+%d%d%d' % (randint(1, 9), randint(100, 999),
                        randint(1000000, 9999999))


def random_zip():
    return str(randint(10000, 99999))


def get_random_avatar(folder):
    """
    Return random avatar file form folder
    """
    avatar = choice(os.listdir(folder))
    return os.path.join(folder, avatar)


class AccountData(object):
    def random_fname(self, *args, **kwargs):
        self.fname = random_fname(*args, **kwargs)
        return self.fname

    def random_lname(self, *args, **kwargs):
        self.lname = random_lname(*args, **kwargs)
        return self.lname

    def random_password(self, *args, **kwargs):
        self.password = random_password(*args, **kwargs)
        return self.password

    def random_login(self, *args, **kwargs):
        self.login = random_login(*args, **kwargs)
        return self.login
