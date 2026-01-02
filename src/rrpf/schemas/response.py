from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .common import RequestID
from .errors import RRPError
from .provenance import Provenance


@dataclass(frozen=True)
class RRPResponse:
    ok: bool
    request_id: RequestID
    as_of: str
    data: Mapping[str, Any]
    partial: bool
    errors: Sequence[RRPError]
    provenance: Provenance
