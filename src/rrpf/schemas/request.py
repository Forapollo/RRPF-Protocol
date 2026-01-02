from dataclasses import dataclass
from datetime import datetime

from .as_of import AsOf
from .common import CorrelationID, RequestID
from .constraints import Constraints
from .data_requests import DataRequests
from .intent import Intent


@dataclass(frozen=True)
class RRPRequest:
    rrp_version: str
    request_id: RequestID
    correlation_id: CorrelationID | None
    requested_at: datetime
    intent: Intent
    as_of: AsOf
    constraints: Constraints
    data: DataRequests
