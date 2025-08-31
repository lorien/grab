from __future__ import annotations

from types import TracebackType
from typing import Tuple, Type

# pylint: disable=deprecated-typing-alias
FatalErrorQueueItem = Tuple[Type[Exception], Exception, TracebackType]
# pylint: enable=deprecated-typing-alias
