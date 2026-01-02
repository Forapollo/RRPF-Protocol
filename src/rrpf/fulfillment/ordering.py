from collections.abc import Callable, Iterable
from typing import TypeVar

from rrpf.normalization.sorting import stable_sorted

T = TypeVar("T")


def stable_order(
    items: Iterable[T],
    *,
    key: Callable[[T], str],
) -> list[T]:
    """Alias of normalization.stable_sorted for engine convenience."""
    return stable_sorted(items, key=key)
