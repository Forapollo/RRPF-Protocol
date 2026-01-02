from datetime import UTC, datetime
from typing import cast

import rrpf
from rrpf.schemas import (
    AsOf,
    Constraints,
    DataRequests,
    EventRequest,
    Intent,
    RRPRequest,
    TableRequest,
)
from rrpf.schemas.as_of import AsOfMode
from rrpf.schemas.common import CorrelationID, RequestID
from rrpf.schemas.intent import IntentMode


def _create_valid_request() -> RRPRequest:
    return RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-valid"),
        correlation_id=cast(CorrelationID, "corr-valid"),
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        intent=Intent(name="test", mode=IntentMode.SNAPSHOT),
        as_of=AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=Constraints(max_total_rows=100, max_groups=10, fail_on_partial=True),
        data=DataRequests(
            tables=[TableRequest(table="t1", fields=["f1"], limit=10, derived=None)],
            events=[],
        ),
    )


def test_valid_request() -> None:
    req = _create_valid_request()
    errors = rrpf.validate_request(req)
    assert len(errors) == 0


def test_invalid_version() -> None:
    req = _create_valid_request()
    # Use object.__setattr__ to bypass frozen dataclass for testing
    object.__setattr__(req, "rrp_version", "2.0")
    errors = rrpf.validate_request(req)
    assert len(errors) == 1
    assert errors[0].code == "invalid_version"


def test_missing_table_limit() -> None:
    req = _create_valid_request()
    table = TableRequest(table="t1", fields=["f1"], limit=0, derived=None)
    object.__setattr__(req.data, "tables", [table])

    errors = rrpf.validate_request(req)
    assert len(errors) == 1
    assert errors[0].code == "invalid_limit"
    assert "limit must be > 0" in errors[0].message


def test_empty_fields() -> None:
    req = _create_valid_request()
    table = TableRequest(table="t1", fields=[], limit=10, derived=None)
    object.__setattr__(req.data, "tables", [table])

    errors = rrpf.validate_request(req)
    assert len(errors) == 1
    assert errors[0].code == "empty_fields"


def test_empty_request() -> None:
    req = _create_valid_request()
    object.__setattr__(req.data, "tables", [])
    object.__setattr__(req.data, "events", [])

    errors = rrpf.validate_request(req)
    assert len(errors) == 1
    assert errors[0].code == "empty_request"


def test_invalid_as_of_combinations() -> None:
    # Test LATEST with timestamp
    req1 = _create_valid_request()
    as_of1 = AsOf(mode=AsOfMode.LATEST, timestamp=datetime.now(UTC))
    object.__setattr__(req1, "as_of", as_of1)

    errors1 = rrpf.validate_request(req1)
    assert len(errors1) == 1
    assert errors1[0].code == "unexpected_timestamp"

    # Test TIMESTAMP without timestamp
    req2 = _create_valid_request()
    as_of2 = AsOf(mode=AsOfMode.TIMESTAMP, timestamp=None)
    object.__setattr__(req2, "as_of", as_of2)

    errors2 = rrpf.validate_request(req2)
    assert len(errors2) == 1
    assert errors2[0].code == "missing_timestamp"


def test_group_overflow() -> None:
    req = _create_valid_request()
    object.__setattr__(req.constraints, "max_groups", 1)

    # 2 tables > 1 max_group
    t1 = TableRequest(table="t1", fields=["f1"], limit=10, derived=None)
    t2 = TableRequest(table="t2", fields=["f1"], limit=10, derived=None)
    object.__setattr__(req.data, "tables", [t1, t2])

    errors = rrpf.validate_request(req)
    assert len(errors) == 1
    assert errors[0].code == "max_groups_exceeded"


def test_invalid_constraints_values() -> None:
    req = _create_valid_request()
    object.__setattr__(req.constraints, "max_total_rows", 0)
    object.__setattr__(req.constraints, "max_groups", 0)

    errors = rrpf.validate_request(req)
    # Expecting errors for both invalid constraints
    codes = [e.code for e in errors]
    assert "invalid_max_total_rows" in codes
    assert "invalid_max_groups" in codes


def test_invalid_event_request() -> None:
    req = _create_valid_request()
    event = EventRequest(types=[], fields=[], limit=0)
    object.__setattr__(req.data, "tables", [])
    object.__setattr__(req.data, "events", [event])

    errors = rrpf.validate_request(req)
    codes = [e.code for e in errors]
    assert "empty_types" in codes
    assert "empty_fields" in codes
    assert "invalid_limit" in codes
