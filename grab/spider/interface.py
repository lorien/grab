from __future__ import annotations

from types import TracebackType
from typing import Tuple, Type

FatalErrorQueueItem = Tuple[Type[Exception], Exception, TracebackType]
