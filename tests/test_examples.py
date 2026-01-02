from datetime import UTC, datetime
from typing import cast

from rrpf import run_fulfillment
from rrpf.examples import InMemoryEngine
from rrpf.schemas.as_of import AsOf, AsOfMode
from rrpf.schemas.common import CorrelationID, RequestID
from rrpf.schemas.constraints import Constraints
from rrpf.schemas.data_requests import DataRequests, TableRequest
from rrpf.schemas.intent import Intent, IntentMode
from rrpf.schemas.request import RRPRequest


def test_memory_engine_example() -> None:
    # 1. Create Request
    req = RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-test"),
        correlation_id=cast(CorrelationID, "corr-test"),
        requested_at=datetime.now(UTC),
        intent=Intent(name="test", mode=IntentMode.SNAPSHOT),
        as_of=AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=Constraints(max_total_rows=100, max_groups=10, fail_on_partial=True),
        data=DataRequests(
            tables=[TableRequest(table="t1", fields=["id"], limit=5, derived=None)],
            events=[],
        ),
    )

    # 2. Instantiate Engine
    engine = InMemoryEngine()

    # 3. Run
    result = run_fulfillment(req, engine)

    # 4. Assert
    assert result.response.ok is True
    assert result.response.partial is False
    assert result.response.errors == []

    # Check Data
    assert "table:t1" in result.response.data
    rows = result.response.data["table:t1"]["rows"]
    # Memory engine returns min(limit, 3) -> min(5, 3) = 3
    assert len(rows) == 3
    assert rows[0] == {"id": 0}

    # Check Stats
    stats = result.response.provenance.query_stats
    assert "table:t1" in stats
    assert stats["table:t1"].rows == 3
    assert stats["table:t1"].groups == 1
