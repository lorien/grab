import json
from copy import deepcopy

DEFAULT_CONFIG = {
    "mongodb_task_queue": {
        "connection_args": {},
    },
    "redis_task_queue": {
        "connection_args": {},
    },
}


def load_config():
    config = deepcopy(DEFAULT_CONFIG)
    try:
        with open("test_config", encoding="utf-8") as inp:
            local_config = json.load(inp)
    except FileNotFoundError:
        pass
    else:
        for key, val in local_config.items():
            if key in DEFAULT_CONFIG:
                raise Exception("Invalid config key: {}".format(key))
            config[key] = val
    return config
