from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .common import Digest


@dataclass(frozen=True)
class QueryStats:
    rows: int
    groups: int

@dataclass(frozen=True)
class Provenance:
    fulfilled_at: datetime
    inputs_digest: Digest
    query_stats: Mapping[str, QueryStats]
