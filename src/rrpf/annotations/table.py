from collections.abc import Callable
from typing import Any, TypeVar

from rrpf.annotations.base import Capability

F = TypeVar("F", bound=Callable[..., Any])

def table(
    name: str,
    *,
    schema: Any,
    max_rows: int,
    description: str | None = None,
) -> Callable[[F], F]:
    if not name:
        raise ValueError("Table name cannot be empty")
    if max_rows <= 0:
        raise ValueError("max_rows must be positive")

    def decorator(func: F) -> F:
        capability = Capability(
            kind="table",
            name=name,
            schema=schema,
            max_items=max_rows,
            description=description,
        )
        func.__rrpf_capability__ = capability  # type: ignore[attr-defined]
        return func

    return decorator
