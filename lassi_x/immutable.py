"""Read-only containers retaining JSON list/dict and pickle compatibility."""

from __future__ import annotations

from typing import Any, Never


def _reject(*args: Any, **kwargs: Any) -> Never:
    raise TypeError("wire message collections are immutable")


class FrozenList[T](list[T]):
    """A JSON-compatible list whose contents cannot change after validation."""

    __setitem__ = _reject
    __delitem__ = _reject
    __iadd__ = _reject
    __imul__ = _reject
    append = _reject
    clear = _reject
    extend = _reject
    insert = _reject
    pop = _reject
    remove = _reject
    reverse = _reject
    sort = _reject

    def __reduce__(self) -> tuple[Any, tuple[list[T]]]:
        return type(self), (list(self),)

    def __deepcopy__(self, memo: dict[int, Any]) -> FrozenList[T]:
        return self


class FrozenDict[K, V](dict[K, V]):
    """A JSON-compatible dictionary with the usual mutation methods disabled."""

    __setitem__ = _reject
    __delitem__ = _reject
    __ior__ = _reject
    clear = _reject
    pop = _reject
    popitem = _reject
    setdefault = _reject
    update = _reject

    def __reduce__(self) -> tuple[Any, tuple[dict[K, V]]]:
        return type(self), (dict(self),)

    def __deepcopy__(self, memo: dict[int, Any]) -> FrozenDict[K, V]:
        return self


def freeze(value: Any) -> Any:
    """Freeze nested containers; nested wire models freeze their own fields."""
    if isinstance(value, dict):
        return FrozenDict({key: freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return FrozenList(freeze(item) for item in value)
    return value
