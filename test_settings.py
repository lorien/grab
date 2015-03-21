MONGODB_CONNECTION = {
    'database': 'test_database',
}

MYSQL_CONNECTION = {
    'database': 'spider_test',
    'user': 'web',
    'passwd': 'web-**',
}

REDIS_CONNECTION = {}

POSTGRESQL_CONNECTION = {
    'database': 'spider_test',
}

try:
    from test_settings_local import *
except ImportError:
    pass
