MONGODB_CONNECTION = {
    'database': 'grab_test',
}

REDIS_CONNECTION = {}

try:
    from test_settings_local import *
except ImportError:
    pass
