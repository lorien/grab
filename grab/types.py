"""Types used in Grab projects and utility functions to deal with these types.

I can not build generic function for combined logic of resolve_transport_entity
and resolve_grab_entity because mypy does not allow to parametrise Generic with
base class.
"""
from __future__ import annotations

import inspect

from .base import BaseExtension, BaseGrab, BaseTransport


def resolve_transport_entity(
    entity: None | BaseTransport | type[BaseTransport],
    default: type[BaseTransport],
) -> BaseTransport:
    if entity and (
        not isinstance(entity, BaseTransport) and not issubclass(entity, BaseTransport)
    ):
        raise TypeError("Invalid BaseTransport entity: {}".format(entity))
    if entity is None:
        return default()
    if isinstance(entity, BaseTransport):
        return entity
    return entity()


def resolve_grab_entity(
    entity: None | BaseGrab | type[BaseGrab], default: type[BaseGrab]
) -> BaseGrab:
    if entity and (
        not isinstance(entity, BaseGrab) and not issubclass(entity, BaseGrab)
    ):
        raise TypeError("Invalid BaseGrab entity: {}".format(entity))
    if entity is None:
        assert issubclass(default, BaseGrab)
        return default()
    if isinstance(entity, BaseGrab):
        return entity
    return entity()


def resolve_extension_entity(
    entity: BaseExtension | type[BaseExtension],
) -> BaseExtension:
    if (
        not entity
        or not isinstance(entity, BaseExtension)
        or (not inspect.isclass(entity) or not issubclass(entity, BaseExtension))
    ):
        raise TypeError("Invalid BaseExtension entity: {}".format(entity))
    return entity if isinstance(entity, BaseExtension) else entity()
