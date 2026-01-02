from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum
from typing import Any, cast

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

from .sorting import stable_sorted


def canonicalize_request(request: RRPRequest) -> Mapping[str, Any]:
    """
    Convert RRPRequest into a canonical, deterministic mapping.
    """
    return cast(Mapping[str, Any], _to_canonical_dict(request))


def _to_canonical_dict(obj: Any) -> Any:
    if isinstance(obj, RRPRequest):
        return {
            "rrp_version": obj.rrp_version,
            "request_id": obj.request_id,
            "correlation_id": obj.correlation_id,
            "requested_at": _canonicalize_datetime(obj.requested_at),
            "intent": _to_canonical_dict(obj.intent),
            "as_of": _canonicalize_as_of(obj.as_of),
            "constraints": _to_canonical_dict(obj.constraints),
            "data": _to_canonical_dict(obj.data),
        }
    elif isinstance(obj, Intent):
        return {
            "name": obj.name,
            "mode": obj.mode.value,
        }
    elif isinstance(obj, Constraints):
        return {
            "max_total_rows": obj.max_total_rows,
            "max_groups": obj.max_groups,
            "fail_on_partial": obj.fail_on_partial,
        }
    elif isinstance(obj, DataRequests):
        return {
            "tables": [
                _to_canonical_dict(t)
                for t in stable_sorted(obj.tables, key=lambda x: x.table)
            ],
            "events": [
                _to_canonical_dict(e)
                for e in stable_sorted(obj.events, key=lambda x: ",".join(sorted(x.types)))
            ],
        }
    elif isinstance(obj, TableRequest):
        return {
            "table": obj.table,
            "fields": sorted(obj.fields),
            "limit": obj.limit,
            "derived": sorted(obj.derived) if obj.derived else None,
        }
    elif isinstance(obj, EventRequest):
        return {
            "types": sorted(obj.types),
            "fields": sorted(obj.fields),
            "limit": obj.limit,
        }
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return _canonicalize_datetime(obj)
    elif obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        raise TypeError(f"Unknown object type: {type(obj)}")


def _canonicalize_datetime(dt: datetime) -> str:
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.isoformat().replace("+00:00", "Z")


def _canonicalize_as_of(as_of: AsOf) -> Mapping[str, Any]:
    if as_of.mode == AsOfMode.LATEST:
        return {
            "mode": as_of.mode.value,
            "timestamp": None,
        }
    elif as_of.mode == AsOfMode.TIMESTAMP:
        if as_of.timestamp is None:
            # Should not happen if validated, but handle gracefully or raise
            raise ValueError("AsOf mode TIMESTAMP requires a timestamp")
        return {
            "mode": as_of.mode.value,
            "timestamp": _canonicalize_datetime(as_of.timestamp),
        }
    else:
        raise ValueError(f"Unknown AsOf mode: {as_of.mode}")
