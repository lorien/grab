class DefaultConfig(object):
    #SPIDER_LOCATIONS = ['spider.py', 'spider/*']
    SPIDER_MODULES = ['spider']
    SAVE_FATAL_ERRORS = True
    SAVE_TASK_ADD_ERRORS = True
    SAVE_FINAL_STATS = True
    THREAD_NUMBER = 1
    NETWORK_TRY_LIMIT = 10
    TASK_TRY_LIMIT = 10
    DISPLAY_TIMING = True
    DISPLAY_STATS = True

default_config = DefaultConfig()
