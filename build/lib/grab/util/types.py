"""Types used in Grab projects and utility functions to deal with these types.

I can not build generic function for combined logic of resolve_transport_entity
and resolve_grab_entity because mypy does not allow to parametrise Generic with
base class.
"""
from __future__ import annotations

import inspect
import typing
from typing import TypeVar, cast

T = TypeVar("T")


def resolve_entity(
    base_type: type[T],
    entity: None | T | type[T],
    default: type[T],
) -> T:
    if entity and (
        not isinstance(entity, base_type)
        and (not inspect.isclass(entity) or not issubclass(entity, base_type))
    ):
        raise TypeError("Invalid {} entity: {}".format(base_type, entity))
    if entity is None:
        assert issubclass(default, base_type)
        return default()
    if isinstance(entity, base_type):
        return entity
    # pylint: disable=deprecated-typing-alias
    return cast(typing.Type[T], entity)()
