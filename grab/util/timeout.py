from __future__ import annotations

from enum import Enum


class UndefinedParam(Enum):
    value = object()


UNDEFINED_PARAM: UndefinedParam = UndefinedParam.value
DEFAULT_TOTAL_TIMEOUT = None


class Timeout:
    __slots__ = ["total", "connect", "read"]

    def __init__(
        self,
        total: None | float | UndefinedParam = UNDEFINED_PARAM,
        connect: None | float | UndefinedParam = UNDEFINED_PARAM,
        read: None | float | UndefinedParam = UNDEFINED_PARAM,
    ) -> None:
        """Timeout constructor.

        Unspecified total timeout is set to None.
        Unspecified connect timeout is set to total timeout.
        Unspecified read timeout is set to total timeout.
        """
        self.total = total if total is not UNDEFINED_PARAM else DEFAULT_TOTAL_TIMEOUT
        self.connect = connect if connect is not UNDEFINED_PARAM else self.total
        self.read = read if read is not UNDEFINED_PARAM else self.total

    def __repr__(self) -> str:
        return "{}(connect={!r}, read={!r}, total={!r})".format(
            type(self).__name__, self.connect, self.read, self.total
        )
