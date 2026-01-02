from dataclasses import dataclass
from datetime import UTC, datetime

from rrpf.fulfillment.engine import FulfillmentEngine
from rrpf.hashing.canonical_json import to_canonical_json
from rrpf.hashing.digest import compute_digest
from rrpf.normalization.canonicalize import canonicalize_request
from rrpf.schemas.as_of import AsOfMode
from rrpf.schemas.common import Digest
from rrpf.schemas.errors import RRPError
from rrpf.schemas.provenance import Provenance
from rrpf.schemas.request import RRPRequest
from rrpf.schemas.response import RRPResponse
from rrpf.storage.payload_store import PayloadStore
from rrpf.validation.validator import validate_request


@dataclass(frozen=True)
class RunResult:
    response: RRPResponse
    canonical_json: str
    digest: Digest


def run_fulfillment(request: RRPRequest, engine: FulfillmentEngine) -> RunResult:
    """
    Orchestrate a full RRPF cycle.
    """
    # 1. Validate request
    validation_errors = validate_request(request)
    if validation_errors:
        rrp_errors = [
            RRPError(
                code=ve.code,
                message=ve.message,
                section=ve.path,
            )
            for ve in validation_errors
        ]
        response = RRPResponse(
            ok=False,
            request_id=request.request_id,
            as_of="unknown",
            partial=False,
            errors=rrp_errors,
            data={},
            provenance=Provenance(
                fulfilled_at=datetime.now(UTC),
                inputs_digest=Digest(""),
                query_stats={},
            ),
        )
        # For invalid requests, we don't produce canonical JSON/digest effectively
        return RunResult(response=response, canonical_json="", digest=Digest(""))

    # 2. Canonicalize + digest
    canonical = canonicalize_request(request)
    canonical_json = to_canonical_json(canonical)
    digest = compute_digest(canonical_json)

    # 3. Call engine
    result = engine.fulfill(request)
    data = dict(result.data)
    stats = dict(result.query_stats)

    errors: list[RRPError] = []

    # 4. Enforce constraints
    total_rows = sum(s.rows for s in stats.values())

    if total_rows > request.constraints.max_total_rows:
        error = RRPError(
            code="max_total_rows_exceeded",
            message=f"Total rows {total_rows} exceeds limit {request.constraints.max_total_rows}",
            section="constraints",
        )
        errors.append(error)
        # If fail_on_partial is True, we fail hard.
        # If False, we continue but include the error and mark partial=True.
        # Logic handled at the end when determining ok/partial status.

    # 5. Partial semantics check
    expected_sections = set()
    for table in request.data.tables:
        expected_sections.add(f"table:{table.table}")
    for event in request.data.events:
        types_key = "+".join(sorted(event.types))
        expected_sections.add(f"event:{types_key}")

    missing_sections = expected_sections - set(data.keys())
    if missing_sections:
        for missing in sorted(missing_sections):
            errors.append(
                RRPError(
                    code="missing_section",
                    message=f"Section {missing} was not fulfilled",
                    section=missing,
                )
            )

    # Determine final status
    is_failed = False
    is_partial = False

    if errors:
        if request.constraints.fail_on_partial:
            is_failed = True
            is_partial = False
        else:
            is_failed = False
            is_partial = True

    # 6. Response shaping
    as_of_str: str
    if request.as_of.mode == AsOfMode.LATEST:
        as_of_str = "latest"
    else:
        # Use same logic as canonicalize for consistency if needed,
        # but spec says "ISO UTC timestamp string (same format as canonicalization)"
        # Canonicalization uses: dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
        # If AsOfMode.TIMESTAMP, timestamp is not None (validated).
        ts = request.as_of.timestamp
        if ts is not None:
            ts = ts.replace(tzinfo=UTC) if ts.tzinfo is None else ts.astimezone(UTC)
            as_of_str = ts.isoformat().replace("+00:00", "Z")
        else:
            # Should not happen given validation, but fallback
            as_of_str = "unknown"

    # Construct final response
    if is_failed:
        response = RRPResponse(
            ok=False,
            request_id=request.request_id,
            as_of=as_of_str,
            partial=False,
            errors=errors,
            data={},
            provenance=Provenance(
                fulfilled_at=datetime.now(UTC),
                inputs_digest=digest,
                query_stats=stats,
            ),
        )
    else:
        response = RRPResponse(
            ok=True,
            request_id=request.request_id,
            as_of=as_of_str,
            partial=is_partial,
            errors=errors,
            data=data,
            provenance=Provenance(
                fulfilled_at=datetime.now(UTC),
                inputs_digest=digest,
                query_stats=stats,
            ),
        )

    return RunResult(
        response=response,
        canonical_json=canonical_json,
        digest=digest,
    )


def run_and_store(
    *,
    request: RRPRequest,
    engine: FulfillmentEngine,
    store: PayloadStore,
) -> RunResult:
    """
    Run fulfillment and persist the payload.
    """
    result = run_fulfillment(request, engine)

    # Only store if validation passed (digest is non-empty)
    # The requirement says "Stores response using digest".
    # Invalid requests have empty digest, which shouldn't be stored or collided.
    if result.digest:
        store.store(digest=result.digest, response=result.response)

    return result
