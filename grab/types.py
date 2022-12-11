from __future__ import annotations

from typing import Any, Callable, Dict, MutableMapping, Optional, Union

from typing_extensions import TypeAlias

NULL = object()
JsonDocument: TypeAlias = Dict[str, Any]
GrabConfig: TypeAlias = MutableMapping[str, Any]
TransportParam: TypeAlias = Optional[Union[str, Callable[..., Any]]]
