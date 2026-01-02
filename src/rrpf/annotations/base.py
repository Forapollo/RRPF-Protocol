from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Capability:
    kind: Literal["table", "event"]
    name: str
    schema: Any
    max_items: int
    description: str | None = None
