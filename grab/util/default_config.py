class DefaultConfig(object):
    GRAB_SPIDER_MODULES = ['spider']
    GRAB_SAVE_REPORT = True
    GRAB_THREAD_NUMBER = 1
    GRAB_NETWORK_TRY_LIMIT = 10
    GRAB_TASK_TRY_LIMIT = 10
    GRAB_DISPLAY_TIMING = False
    GRAB_DISPLAY_STATS = True
    GRAB_ACTIVATE_VIRTUALENV = False
    GRAB_DJANGO_SETTINGS = None

default_config = DefaultConfig()
