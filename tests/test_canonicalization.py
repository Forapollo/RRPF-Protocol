from datetime import UTC, datetime
from typing import cast

import pytest

import rrpf
from rrpf.schemas.as_of import AsOfMode
from rrpf.schemas.common import CorrelationID, RequestID
from rrpf.schemas.intent import IntentMode


def _create_sample_request() -> rrpf.RRPRequest:
    return rrpf.RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-1"),
        correlation_id=cast(CorrelationID, "corr-1"),
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        intent=rrpf.Intent(name="audit", mode=IntentMode.AUDIT),
        as_of=rrpf.AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=rrpf.Constraints(
            max_total_rows=100,
            max_groups=10,
            fail_on_partial=True
        ),
        data=rrpf.DataRequests(
            tables=[
                rrpf.TableRequest(
                    table="users",
                    fields=["id", "email"],
                    limit=10,
                    derived=None
                ),
                rrpf.TableRequest(
                    table="accounts",
                    fields=["id", "balance"],
                    limit=5,
                    derived=["total"]
                )
            ],
            events=[
                rrpf.EventRequest(
                    types=["login", "logout"],
                    fields=["ts", "user_id"],
                    limit=50
                )
            ]
        )
    )


def test_canonicalization_structure() -> None:
    req = _create_sample_request()
    canonical = rrpf.canonicalize_request(req)

    assert isinstance(canonical, dict)
    assert canonical["rrp_version"] == "1.0"
    assert canonical["intent"]["mode"] == "audit"
    assert canonical["as_of"]["timestamp"] is None
    assert canonical["requested_at"] == "2023-01-01T12:00:00+00:00".replace("+00:00", "Z")


def test_semantic_equality_reordered_fields() -> None:
    # Original request
    req1 = _create_sample_request()

    # Same request but with reordered fields in TableRequest and EventRequest
    req2 = rrpf.RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-1"),
        correlation_id=cast(CorrelationID, "corr-1"),
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        intent=rrpf.Intent(name="audit", mode=IntentMode.AUDIT),
        as_of=rrpf.AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=rrpf.Constraints(
            max_total_rows=100,
            max_groups=10,
            fail_on_partial=True
        ),
        data=rrpf.DataRequests(
            tables=[
                rrpf.TableRequest(
                    table="users",
                    fields=["email", "id"],  # Reordered
                    limit=10,
                    derived=None
                ),
                rrpf.TableRequest(
                    table="accounts",
                    fields=["balance", "id"],  # Reordered
                    limit=5,
                    derived=["total"]
                )
            ],
            events=[
                rrpf.EventRequest(
                    types=["logout", "login"],  # Reordered
                    fields=["user_id", "ts"],  # Reordered
                    limit=50
                )
            ]
        )
    )

    json1 = rrpf.to_canonical_json(rrpf.canonicalize_request(req1))
    json2 = rrpf.to_canonical_json(rrpf.canonicalize_request(req2))

    assert json1 == json2
    assert rrpf.compute_digest(json1) == rrpf.compute_digest(json2)


def test_semantic_equality_reordered_tables() -> None:
    req1 = _create_sample_request()

    # Same request but tables list reordered
    req2 = rrpf.RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-1"),
        correlation_id=cast(CorrelationID, "corr-1"),
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        intent=rrpf.Intent(name="audit", mode=IntentMode.AUDIT),
        as_of=rrpf.AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=rrpf.Constraints(
            max_total_rows=100,
            max_groups=10,
            fail_on_partial=True
        ),
        data=rrpf.DataRequests(
            tables=[
                rrpf.TableRequest(
                    table="accounts",  # Swapped order
                    fields=["id", "balance"],
                    limit=5,
                    derived=["total"]
                ),
                rrpf.TableRequest(
                    table="users",
                    fields=["id", "email"],
                    limit=10,
                    derived=None
                )
            ],
            events=[
                rrpf.EventRequest(
                    types=["login", "logout"],
                    fields=["ts", "user_id"],
                    limit=50
                )
            ]
        )
    )

    json1 = rrpf.to_canonical_json(rrpf.canonicalize_request(req1))
    json2 = rrpf.to_canonical_json(rrpf.canonicalize_request(req2))

    assert json1 == json2


def test_as_of_normalization() -> None:
    # Test LATEST
    # We need a full request to pass to canonicalize_request, but we can check internal logic
    # or just check the output part.
    req_latest = _create_sample_request()
    canonical_latest = rrpf.canonicalize_request(req_latest)
    assert canonical_latest["as_of"] == {"mode": "latest", "timestamp": None}

    # Test TIMESTAMP
    ts = datetime(2023, 6, 1, 10, 0, 0, tzinfo=UTC)
    as_of_ts = rrpf.AsOf(mode=AsOfMode.TIMESTAMP, timestamp=ts)
    req_ts = rrpf.RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-2"),
        correlation_id=None,
        requested_at=datetime.now(UTC),
        intent=rrpf.Intent(name="hist", mode=IntentMode.SNAPSHOT),
        as_of=as_of_ts,
        constraints=rrpf.Constraints(1, 1, False),
        data=rrpf.DataRequests([], [])
    )
    canonical_ts = rrpf.canonicalize_request(req_ts)
    assert canonical_ts["as_of"]["mode"] == "timestamp"
    assert canonical_ts["as_of"]["timestamp"] == "2023-06-01T10:00:00Z"


def test_digest_stability() -> None:
    req = _create_sample_request()
    canonical = rrpf.canonicalize_request(req)
    json_str = rrpf.to_canonical_json(canonical)
    digest1 = rrpf.compute_digest(json_str)
    digest2 = rrpf.compute_digest(json_str)

    assert digest1 == digest2
    # Verify it looks like a sha256 hex digest
    assert len(digest1) == 64
    try:
        int(digest1, 16)
    except ValueError:
        pytest.fail("Digest is not valid hex")


def test_no_mutation() -> None:
    req = _create_sample_request()
    # Capture state
    original_tables = list(req.data.tables)
    original_fields_0 = list(req.data.tables[0].fields)

    _ = rrpf.canonicalize_request(req)

    # Verify strict equality
    assert req.data.tables == original_tables
    assert req.data.tables[0].fields == original_fields_0
