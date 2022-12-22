from __future__ import annotations

from typing import Any, Dict, MutableMapping

from typing_extensions import TypeAlias

NULL = object()
# pylint: disable=deprecated-typing-alias, consider-alternative-union-syntax
JsonDocument: TypeAlias = Dict[str, Any]
GrabConfig: TypeAlias = MutableMapping[str, Any]
# pylint: enable=deprecated-typing-alias, consider-alternative-union-syntax
