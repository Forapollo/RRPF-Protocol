from collections.abc import Mapping
from typing import Any, Protocol

from rrpf.schemas.provenance import QueryStats
from rrpf.schemas.request import RRPRequest


class FulfillmentResult(Protocol):
    @property
    def data(self) -> Mapping[str, Any]: ...
    @property
    def query_stats(self) -> Mapping[str, QueryStats]: ...


class FulfillmentEngine(Protocol):
    def fulfill(self, request: RRPRequest) -> FulfillmentResult:
        """
        MUST only fulfill what is explicitly requested.
        MUST respect all per-group limits.
        MUST return deterministic ordering.
        """
        ...
