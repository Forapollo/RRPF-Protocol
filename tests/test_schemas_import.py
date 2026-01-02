from datetime import UTC, datetime
from typing import cast

import rrpf
from rrpf.schemas.as_of import AsOfMode
from rrpf.schemas.common import CorrelationID, Digest, RequestID
from rrpf.schemas.intent import IntentMode


def test_schema_instantiation() -> None:
    # 1. Intent
    intent = rrpf.Intent(name="test_intent", mode=IntentMode.SNAPSHOT)
    assert intent.name == "test_intent"

    # 2. AsOf
    as_of = rrpf.AsOf(mode=AsOfMode.LATEST, timestamp=None)
    assert as_of.mode == AsOfMode.LATEST

    # 3. Constraints
    constraints = rrpf.Constraints(
        max_total_rows=100,
        max_groups=10,
        fail_on_partial=True
    )
    assert constraints.max_total_rows == 100

    # 4. DataRequests
    table_req = rrpf.TableRequest(
        table="users",
        fields=["id", "name"],
        limit=10,
        derived=None
    )
    event_req = rrpf.EventRequest(
        types=["login"],
        fields=["timestamp", "user_id"],
        limit=50
    )
    data_reqs = rrpf.DataRequests(
        tables=[table_req],
        events=[event_req]
    )
    assert len(data_reqs.tables) == 1

    # 5. RRPRequest
    req_id = cast(RequestID, "req-123")
    corr_id = cast(CorrelationID, "corr-456")
    request = rrpf.RRPRequest(
        rrp_version="1.0",
        request_id=req_id,
        correlation_id=corr_id,
        requested_at=datetime.now(UTC),
        intent=intent,
        as_of=as_of,
        constraints=constraints,
        data=data_reqs
    )
    assert request.rrp_version == "1.0"

    # 6. Errors
    error = rrpf.RRPError(
        code="ERR_001",
        message="Something went wrong",
        section="data"
    )
    assert error.code == "ERR_001"

    # 7. Provenance
    digest = cast(Digest, "sha256:abcdef")
    provenance = rrpf.Provenance(
        fulfilled_at=datetime.now(UTC),
        inputs_digest=digest,
        query_stats={"users": rrpf.schemas.provenance.QueryStats(rows=10, groups=1)}
    )
    assert provenance.inputs_digest == digest

    # 8. RRPResponse
    response = rrpf.RRPResponse(
        ok=True,
        request_id=req_id,
        as_of="latest",
        data={"users": [{"id": 1}]},
        partial=False,
        errors=[error],
        provenance=provenance
    )
    assert response.ok is True
