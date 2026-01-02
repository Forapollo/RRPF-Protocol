from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class TableRequest:
    table: str
    fields: Sequence[str]
    limit: int
    derived: Sequence[str] | None

@dataclass(frozen=True)
class EventRequest:
    types: Sequence[str]
    fields: Sequence[str]
    limit: int

@dataclass(frozen=True)
class DataRequests:
    tables: Sequence[TableRequest]
    events: Sequence[EventRequest]
