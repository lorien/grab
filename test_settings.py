MONGODB_CONNECTION = {
    'database': 'test_database',
}

MYSQL_CONNECTION = {
    'database': 'spider_test',
    'user': 'web',
    'passwd': 'web-**',
}

REDIS_CONNECTION = {}

try:
    from test_settings_local import *
except ImportError:
    pass
