# Quickstart

## Installation

```bash
pip install rrpf-protocol
```

## Usage

This example demonstrates how to create a request, fulfill it using the reference in-memory engine, and inspect the response.

```python
from datetime import UTC, datetime
from rrpf import (
    RRPRequest, Intent, AsOf, Constraints, DataRequests, TableRequest,
    run_fulfillment
)
from rrpf.examples import InMemoryEngine
from rrpf.schemas.as_of import AsOfMode
from rrpf.schemas.intent import IntentMode

# 1. Create a minimal request
request = RRPRequest(
    rrp_version="1.0",
    request_id="req-123",
    correlation_id="corr-abc",
    requested_at=datetime.now(UTC),
    intent=Intent(name="quickstart", mode=IntentMode.SNAPSHOT),
    as_of=AsOf(mode=AsOfMode.LATEST, timestamp=None),
    constraints=Constraints(max_total_rows=100, max_groups=10, fail_on_partial=True),
    data=DataRequests(
        tables=[TableRequest(table="users", fields=["id"], limit=5, derived=None)],
        events=[]
    )
)

# 2. Instantiate the reference engine
# The InMemoryEngine generates deterministic synthetic data for any table.
engine = InMemoryEngine()

# 3. Run fulfillment
# This step validates, canonicalizes, executes the engine, and enforces constraints.
result = run_fulfillment(request, engine)
response = result.response

# 4. Inspect results
print(f"Status: {'OK' if response.ok else 'Failed'}")
print(f"Partial: {response.partial}")
print(f"Digest: {response.provenance.inputs_digest}")

if response.ok:
    print("\nData Received:")
    for section, content in response.data.items():
        print(f"Section: {section}")
        print(f"Rows: {content['rows']}")
else:
    print("\nErrors:")
    for error in response.errors:
        print(f"{error.code}: {error.message}")
```
