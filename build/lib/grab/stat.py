"""Provides Stat class to collect statistics about events is being happening."""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any


class Stat:  # pylint: disable=too-many-instance-attributes
    default_speed_key = "spider:request-processed"
    default_logging_period = 1

    def __init__(
        self,
        logger_name: str = "grab.stat",
        log_file: None | str = None,
        logging_period: int = default_logging_period,
        speed_key: str = default_speed_key,
        extra_speed_keys: None | list[str] = None,
    ) -> None:
        self.speed_key = speed_key
        self.setup_speed_keys(speed_key, extra_speed_keys)
        self.time = time.time()
        self.logging_ignore_prefixes = ["spider:", "parser:"]
        self.logging_period = logging_period
        self.count_prev = 0
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.log_file: None | str = None
        self.setup_logging_file(log_file)
        self.counters: dict[str, int] = defaultdict(int)
        self.collections: dict[str, list[Any]] = defaultdict(list)
        self.counters_prev: dict[str, int] = defaultdict(int)
        self.reset()

    def setup_speed_keys(
        self, speed_key: str, extra_keys: None | list[str] = None
    ) -> None:
        keys = [speed_key]
        if extra_keys:
            keys.extend(extra_keys)
        self.speed_keys = keys

    def reset(self) -> None:
        self.counters.clear()
        self.collections.clear()
        self.counters_prev.clear()

    def setup_logging_file(self, log_file: None | str) -> None:
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

    def get_speed_line(self, now: float | int) -> str:
        items = []
        for key in self.speed_keys:
            time_elapsed = now - self.time
            if not time_elapsed:
                qps: float = 0
            else:
                count_current = self.counters[key]
                diff = count_current - self.counters_prev[key]
                qps = diff / time_elapsed
                self.counters_prev[key] = count_current
            label = "RPS" if (key == self.speed_key) else key
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
