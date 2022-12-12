from __future__ import annotations

import re
import typing
from collections.abc import Callable, Mapping
from re import Pattern
from typing import Union, cast


def test_callable(inp: Callable[..., str | bytes | None]) -> Callable[..., str | bytes]:
    dup: Callable[..., str | bytes] = cast(
        # pylint: disable=deprecated-typing-alias, consider-alternative-union-syntax
        typing.Callable[..., typing.Union[str, bytes]],
        inp
        # pylint: enable=deprecated-typing-alias, consider-alternative-union-syntax
    )
    return dup  # noqa


# def test_union(inp: str | None) -> str | None:
#    dup: str | None = inp
#    return dup

# def test_mutable_mapping(inp: MutableMapping[str, int]) -> MutableMapping[str, float]:
#    dup: MutableMapping[str, int] = inp
#    return cast(
#        typing.MutableMapping[str, float],  # pylint: disable=deprecated-typing-alias
#        dup,
#    )
#
def test_re_pattern(
    inp: Pattern[str] | Pattern[bytes] | None,
) -> Pattern[str] | Pattern[bytes]:
    dup: Pattern[str] | Pattern[bytes] = cast(
        # pylint: disable=deprecated-typing-alias, consider-alternative-union-syntax
        Union[typing.Pattern[str], typing.Pattern[bytes]],
        inp
        # pylint: enable=deprecated-typing-alias, consider-alternative-union-syntax
    )
    return dup  # noqa


def test_isinstance_generic(inp: Mapping[str, int]) -> bool:
    return isinstance(inp, typing.Mapping[str, int])


def main() -> None:
    test_callable(lambda: "foo")
    test_re_pattern(re.compile("foo"))
    test_isinstance_generic({"foo": 1})
    # test_union("foo")
    # test_union(None)
    # test_mutable_mapping({"foo": 1})


if __name__ == "__main__":
    main()
