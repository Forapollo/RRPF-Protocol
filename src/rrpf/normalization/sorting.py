from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")

def stable_sorted(
    items: Iterable[T],
    *,
    key: Callable[[T], str]
) -> list[T]:
    """
    Deterministically sort items by a stable string key.
    """
    return sorted(items, key=key)
