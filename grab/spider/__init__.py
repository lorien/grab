from .base import Spider
from .errors import *  # pylint: disable=wildcard-import
from .task import Task

__all__ = ["Spider", "Task"]
