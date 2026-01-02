from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import rrpf
from rrpf.fulfillment.engine import FulfillmentEngine, FulfillmentResult
from rrpf.schemas.as_of import AsOf, AsOfMode
from rrpf.schemas.common import CorrelationID, Digest, RequestID
from rrpf.schemas.constraints import Constraints
from rrpf.schemas.data_requests import DataRequests, TableRequest
from rrpf.schemas.intent import Intent, IntentMode
from rrpf.schemas.provenance import QueryStats
from rrpf.schemas.request import RRPRequest


@dataclass
class InMemoryResult:
    data: Mapping[str, Any]
    query_stats: Mapping[str, QueryStats]


class InMemoryEngine(FulfillmentEngine):
    def __init__(self, skip_sections: list[str] | None = None) -> None:
        self.skip_sections = set(skip_sections or [])

    def fulfill(self, request: RRPRequest) -> FulfillmentResult:
        data: dict[str, Any] = {}
        stats: dict[str, QueryStats] = {}

        # Handle Tables
        for table in request.data.tables:
            section_key = f"table:{table.table}"
            if section_key in self.skip_sections:
                continue

            # Create dummy rows based on limit
            rows = [{"id": i, "val": "test"} for i in range(min(table.limit, 2))]
            data[section_key] = {"rows": rows}
            stats[section_key] = QueryStats(rows=len(rows), groups=1)

        # Handle Events
        for event in request.data.events:
            types_key = "+".join(sorted(event.types))
            section_key = f"event:{types_key}"
            if section_key in self.skip_sections:
                continue

            rows = [{"ts": "2023-01-01", "type": "t"} for i in range(min(event.limit, 2))]
            data[section_key] = {"rows": rows}
            stats[section_key] = QueryStats(rows=len(rows), groups=1)

        return InMemoryResult(data=data, query_stats=stats)


def _create_request() -> RRPRequest:
    return RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-1"),
        correlation_id=cast(CorrelationID, "corr-1"),
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        intent=Intent(name="test", mode=IntentMode.SNAPSHOT),
        as_of=AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=Constraints(max_total_rows=100, max_groups=10, fail_on_partial=True),
        data=DataRequests(
            tables=[TableRequest(table="t1", fields=["f1"], limit=10, derived=None)],
            events=[],
        ),
    )


def test_happy_path() -> None:
    req = _create_request()
    engine = InMemoryEngine()
    result = rrpf.run_fulfillment(req, engine)

    assert result.response.ok is True
    assert result.response.partial is False
    assert result.response.errors == []
    assert result.response.data is not None
    assert "table:t1" in result.response.data

    prov = result.response.provenance
    assert prov is not None
    assert prov.inputs_digest == result.digest
    assert prov.inputs_digest != Digest("")
    assert "table:t1" in prov.query_stats
    assert prov.query_stats["table:t1"].rows == 2


def test_validation_failure() -> None:
    req = _create_request()
    # Invalidate version
    object.__setattr__(req, "rrp_version", "2.0")

    engine = InMemoryEngine()
    result = rrpf.run_fulfillment(req, engine)

    assert result.response.ok is False
    assert result.response.partial is False
    assert result.response.errors is not None
    assert len(result.response.errors) > 0
    assert result.response.errors[0].code == "invalid_version"

    # Digest should be empty on validation failure per spec
    assert result.digest == Digest("")
    assert result.response.provenance.inputs_digest == Digest("")


def test_missing_section_partial_allowed() -> None:
    req = _create_request()
    # Set fail_on_partial to False
    object.__setattr__(req.constraints, "fail_on_partial", False)

    # Skip the only requested table
    engine = InMemoryEngine(skip_sections=["table:t1"])
    result = rrpf.run_fulfillment(req, engine)

    assert result.response.ok is True
    assert result.response.partial is True
    assert result.response.errors is not None
    assert len(result.response.errors) == 1
    assert result.response.errors[0].code == "missing_section"
    assert result.response.errors[0].section is not None
    assert "table:t1" in result.response.errors[0].section


def test_missing_section_partial_failure() -> None:
    req = _create_request()
    # fail_on_partial is True by default in _create_request

    engine = InMemoryEngine(skip_sections=["table:t1"])
    result = rrpf.run_fulfillment(req, engine)

    assert result.response.ok is False
    assert result.response.partial is False
    assert result.response.errors is not None
    assert len(result.response.errors) == 1
    assert result.response.errors[0].code == "missing_section"


def test_max_total_rows_exceeded() -> None:
    req = _create_request()
    # Set max rows to 1, but engine returns 2 rows
    object.__setattr__(req.constraints, "max_total_rows", 1)

    engine = InMemoryEngine()
    result = rrpf.run_fulfillment(req, engine)

    assert result.response.ok is False
    assert result.response.partial is False
    assert result.response.errors is not None
    codes = [e.code for e in result.response.errors]
    assert "max_total_rows_exceeded" in codes
