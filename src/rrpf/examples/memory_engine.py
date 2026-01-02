from collections.abc import Mapping
from typing import Any

from rrpf.fulfillment.engine import FulfillmentEngine, FulfillmentResult
from rrpf.schemas.provenance import QueryStats
from rrpf.schemas.request import RRPRequest


class InMemoryResult:
    """Concrete implementation of FulfillmentResult."""

    def __init__(
        self,
        data: Mapping[str, Any],
        query_stats: Mapping[str, QueryStats],
    ) -> None:
        self._data = data
        self._query_stats = query_stats

    @property
    def data(self) -> Mapping[str, Any]:
        return self._data

    @property
    def query_stats(self) -> Mapping[str, QueryStats]:
        return self._query_stats


class InMemoryEngine(FulfillmentEngine):
    """
    A reference in-memory engine that generates deterministic synthetic data.
    Useful for testing and validating the protocol flow without external dependencies.
    """

    def fulfill(self, request: RRPRequest) -> FulfillmentResult:
        data: dict[str, Any] = {}
        stats: dict[str, QueryStats] = {}

        # 1. Handle Tables
        for table in request.data.tables:
            section_key = f"table:{table.table}"

            # Generate deterministic rows: min(limit, 3)
            # Each row: {"id": i}
            limit = table.limit
            count = min(limit, 3)
            rows = [{"id": i} for i in range(count)]

            data[section_key] = {"rows": rows}
            stats[section_key] = QueryStats(rows=len(rows), groups=1)

        # 2. Handle Events
        for event in request.data.events:
            # key: event:{'+'.join(sorted(types))}
            types_key = "+".join(sorted(event.types))
            section_key = f"event:{types_key}"

            limit = event.limit
            count = min(limit, 3)
            # Simple synthetic event rows
            event_rows: list[dict[str, Any]] = [
                {"id": i, "type": event.types[0] if event.types else "unknown"}
                for i in range(count)
            ]

            data[section_key] = {"rows": event_rows}
            stats[section_key] = QueryStats(rows=len(event_rows), groups=1)

        return InMemoryResult(data=data, query_stats=stats)
