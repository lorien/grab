"""
This module contains `DeprecatedThingsSpiderMixin` class
that add back-ward compatibility support into `Spider` class

Supported deprecated methods:
    * add_item
    * inc_count
    * start_timer
    * stop_timer
    * setup_grab
    * valid_response_code

Supported deprecated attributes:
    * items
    * counters
    * grab_config
    * taskq

Supported deprecated context managers
    * save_timer
"""
from contextlib import contextmanager

from grab.util.warning import warn


class DeprecatedThingsSpiderMixin(object):
    base_url = None

    def add_item(self, list_name, item):
        warn('Method `Spider::add_item` is deprecated. '
             'Use `Spider::stat.collect` method instead.')
        self.stat.collect(list_name, item)

    def inc_count(self, key, count=1):
        warn('Method `Spider::inc_count` is deprecated. '
             'Use `Spider::stat.inc` method instead.')
        self.stat.inc(key, count)

    def start_timer(self, key):
        warn('Method `Spider::start_timer` is deprecated. '
             'Use `Spider::timer.start` method instead.')
        self.timer.start(key)

    def stop_timer(self, key):
        warn('Method `Spider::stop_timer` is deprecated. '
             'Use `Spider::timer.stop` method instead.')
        self.timer.stop(key)

    @property
    def items(self):
        warn('Attribute `Spider::items` is deprecated. '
             'Use `Spider::stat.collections` attribute instead.')
        return self.stat.collections

    @property
    def counters(self):
        warn('Attribute `Spider::counters` is deprecated. '
             'Use `Spider::stat.counters` attribute instead.')
        return self.stat.counters

    @contextmanager
    def save_timer(self, key):
        warn('Method `Spider::save_timer` is deprecated. '
             'Use `Spider::timer.log_time` method instead.')
        self.timer.start(key)
        try:
            yield
        finally:
            self.timer.stop(key)

    def get_grab_config(self):
        warn('Using `grab_config` attribute is deprecated. Override '
             '`create_grab_instance method instead.')
        return self._grab_config

    def set_grab_config(self, val):
        warn('Using `grab_config` attribute is deprecated. Override '
             '`create_grab_instance method instead.')
        self._grab_config = val

    grab_config = property(get_grab_config, set_grab_config)

    def setup_grab(self, **kwargs):
        warn('Method `Spider::setup_grab` is deprecated. '
             'Define `Spider::create_grab_instance` or '
             'Spider::update_grab_instance` methods in your '
             'Spider sub-class.')
        self.grab_config.update(**kwargs)

    def valid_response_code(self, code, task):
        warn('Method `Spider::valid_response_code` is deprecated. '
             'Use `Spider::is_valid_network_response_code` method or '
             '`Spider::is_valid_network_result` method.')
        return self.is_valid_network_response_code(code, task)

    @property
    def taskq(self):
        warn('Attribute `Spider::taskq` is deprecated. '
             'Use `Spider::task_queue` attribute.')
        return self.task_queue
