MONGODB_CONNECTION = {
    'database': 'grab_test',
}

MYSQL_CONNECTION = {
    'database': 'grab_test',
    'user': 'root',
    'passwd': '',
}

REDIS_CONNECTION = {}

POSTGRESQL_CONNECTION = {
    'database': 'grab_test',
}

try:
    from test_settings_local import *
except ImportError:
    pass
