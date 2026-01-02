# RRPF Protocol

[![PyPI version](https://img.shields.io/pypi/v/rrpf-protocol.svg)](https://pypi.org/project/rrpf-protocol/)
![Python Versions](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **RRPF is a deterministic protocol for explicitly scoped request fulfillment and immutable, replayable reasoning payloads.**

RRPF defines a strict contract for how data requests are expressed, fulfilled, hashed, and persisted. It ensures that any two requests with identical semantic intent produce identical cryptographic digests, enabling perfect cacheability, auditability, and replay of complex data interactions.

## Who this is for

*   **Backend Engineers** building systems that need strict request/response contracts.
*   **Infrastructure & Data Engineers** who need deterministic data fetching and caching layers.
*   **System Architects** requiring absolute reproducibility and auditability of data flows.

## Who this is NOT for

*   **Not an agent framework** — RRPF handles the data layer, not the agency.
*   **Not a workflow engine** — It defines the protocol, not the execution graph.
*   **Not an LLM system** — It provides the ground truth that LLMs reason over.

## Quick Example

```python
from datetime import datetime, timezone
from rrpf import RRPRequest, run_fulfillment
from rrpf.examples import InMemoryEngine
from rrpf.schemas.common import RequestID
from rrpf.schemas.intent import Intent, IntentMode
from rrpf.schemas.as_of import AsOf, AsOfMode
from rrpf.schemas.constraints import Constraints
from rrpf.schemas.data_requests import DataRequests, TableRequest

# 1. Construct a deterministic request
req = RRPRequest(
    rrp_version="1.0",
    request_id=RequestID("example-001"),
    correlation_id=None,
    requested_at=datetime.now(timezone.utc),
    intent=Intent(name="example", mode=IntentMode.SNAPSHOT),
    as_of=AsOf(mode=AsOfMode.LATEST, timestamp=None),
    constraints=Constraints(max_total_rows=100, max_groups=5, fail_on_partial=True),
    data=DataRequests(
        tables=[TableRequest(table="users", fields=["id", "status"], limit=5, derived=None)],
        events=[]
    )
)

# 2. Run fulfillment against an engine
engine = InMemoryEngine()
result = run_fulfillment(req, engine)

# 3. Verify provenance
assert result.response.ok is True
print(f"Inputs Digest: {result.response.provenance.inputs_digest}")
# Output: Inputs Digest: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (example)
```

## Documentation

*   [Quickstart Guide](docs/quickstart.md)
*   [Engine Implementation Guide](docs/engines.md)
*   [Versioning Policy](VERSIONING.md)
*   [Changelog](CHANGELOG.md)

## Guarantees

*   **Deterministic Canonicalization**: Semantically identical requests always hash to the same digest.
*   **Immutable Replay**: Payloads are digest-addressed and never re-executed upon replay.
*   **Engine Agnostic**: The protocol works with any backend (Memory, SQLite, Postgres, HTTP).
*   **Strict Validation**: Invalid requests are rejected before execution begins.
