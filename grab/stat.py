"""Provides Stat class to collect statistics about events is being happening."""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Generator, Optional, Union

from grab.util.warning import warn

DEFAULT_SPEED_KEY = "spider:request-processed"
DEFAULT_LOGGING_PERIOD = 1


class Stat:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        logger_name: str = "grab.stat",
        log_file: Optional[str] = None,
        logging_period: int = DEFAULT_LOGGING_PERIOD,
        speed_key: str = DEFAULT_SPEED_KEY,
        extra_speed_keys: Optional[list[str]] = None,
    ) -> None:
        self.speed_key = speed_key
        self.setup_speed_keys(speed_key, extra_speed_keys)
        self.time = time.time()
        self.logging_ignore_prefixes = ["spider:", "parser:"]
        self.logging_period = logging_period
        self.count_prev = 0
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.setup_logging_file(log_file)
        self.reset()

    def setup_speed_keys(self, speed_key: str, extra_keys: list[str]) -> None:
        keys = [speed_key]
        if extra_keys:
            keys.extend(extra_keys)
        self.speed_keys = keys

    def reset(self) -> None:
        self.counters = defaultdict(int)
        self.collections = defaultdict(list)
        self.counters_prev = defaultdict(int)

    def setup_logging_file(self, log_file: str) -> None:
        self.log_file = log_file
        if log_file:
            self.logger.addHandler(logging.FileHandler(log_file, "w"))
            self.logger.setLevel(logging.DEBUG)

    def get_counter_line(self) -> str:
        result = []
        for key in list(self.counters.keys()):
            if not any(key.startswith(x) for x in self.logging_ignore_prefixes):
                result.append((key, "%s=%d" % (key, self.counters[key])))
        for key in list(self.collections.keys()):
            if not any(key.startswith(x) for x in self.logging_ignore_prefixes):
                result.append((key, "%s=%d" % (key, len(self.collections[key]))))
        tokens = [x[1] for x in sorted(result, key=lambda x: x[0])]
        return ", ".join(tokens)

    def get_speed_line(self, now: Union[float, int]) -> str:
        items = []
        for key in self.speed_keys:
            time_elapsed = now - self.time
            if time_elapsed == 0:
                qps = 0
            else:
                count_current = self.counters[key]
                diff = count_current - self.counters_prev[key]
                qps = diff / time_elapsed
                self.counters_prev[key] = count_current
            if key == self.speed_key:
                label = "RPS"
            else:
                label = key
            items.append("%s: %.2f" % (label, qps))
        return ", ".join(items)

    def print_progress_line(self) -> None:
        now = time.time()
        self.logger.debug("%s [%s]", self.get_speed_line(now), self.get_counter_line())

    def inc(self, key: str, delta: int = 1) -> None:
        self.counters[key] += delta
        now = time.time()
        if self.logging_period and now - self.time > self.logging_period:
            self.print_progress_line()
            self.time = now

    def collect(self, key: str, val: Any) -> None:
        self.collections[key].append(val)

    def append(self, key: str, val: Any) -> None:
        warn(
            "Method `Stat::append` is deprecated. "
            "Use `Stat::collect` method instead."
        )
        self.collect(key, val)


class Timer:
    def __init__(self) -> None:
        self.time_points = {}
        self.timers = defaultdict(int)

    def start(self, key: str) -> None:
        self.time_points[key] = time.time()

    def stop(self, key: str) -> float:
        elapsed = time.time() - self.time_points[key]
        self.timers[key] += elapsed
        del self.time_points[key]
        return elapsed

    def inc_timer(self, key: str, value: Union[int, float]) -> None:
        self.timers[key] += value

    @contextmanager
    def log_time(self, key: str) -> Generator[None, None, None]:
        # Threadsafe
        start = time.time()
        try:
            yield
        finally:
            self.timers[key] += time.time() - start
