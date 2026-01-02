from collections.abc import Callable
from typing import Any, TypeVar

from rrpf.annotations.base import Capability

F = TypeVar("F", bound=Callable[..., Any])

def event(
    name: str,
    *,
    schema: Any,
    max_events: int,
    description: str | None = None,
) -> Callable[[F], F]:
    if not name:
        raise ValueError("Event name cannot be empty")
    if max_events <= 0:
        raise ValueError("max_events must be positive")

    def decorator(func: F) -> F:
        capability = Capability(
            kind="event",
            name=name,
            schema=schema,
            max_items=max_events,
            description=description,
        )
        func.__rrpf_capability__ = capability  # type: ignore[attr-defined]
        return func

    return decorator
