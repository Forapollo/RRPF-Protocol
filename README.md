# RRPF Protocol

**A deterministic protocol for explicitly scoped request fulfillment and immutable, replayable reasoning payloads.**

[![PyPI version](https://img.shields.io/pypi/v/rrpf-protocol.svg)](https://pypi.org/project/rrpf-protocol/)
![Python Versions](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## How RRPF Works

![How RRPF Works](docs/assets/rrpf_overview.png)

---

## The Problem

Modern reasoning systems and LLM-based applications suffer from a critical systems engineering flaw: **unbounded context and non-deterministic inputs**.

When an application requests data for reasoning, the scope of that data is often implicit, the retrieval logic is opaque, and the exact state of the world at the moment of inference is lost. This leads to:

*   **Non-deterministic payloads**: The same request yields different data at different times, breaking reproducibility.
*   **Unbounded reasoning**: Without explicit constraints, reasoning engines consume unpredictable amounts of context, leading to cost overruns and hallucination.
*   **Audit failures**: It becomes impossible to prove exactly what information was available to a system when a specific decision was made.

These are not AI problems; they are systems problems. They require a strict protocol for defining, bounding, and fulfilling data requirements.

## What RRPF Is

RRPF (Reasoning Request & Fulfillment Protocol) is a formal specification and reference implementation designed to solve these state management issues.

*   **Deterministic**: Identical requests always produce identical cryptographic digests.
*   **Engine-Agnostic**: The protocol defines the interface; the implementation (SQL, Vector DB, API) is swappable.
*   **Schema-First**: All interactions are governed by strict, versioned schemas.
*   **Replayable**: Every fulfilled response carries a digest that allows for bit-perfect replay of the reasoning context.
*   **Cryptographically Addressed**: Payloads are identified by the hash of their inputs and configuration, not by arbitrary IDs.

## What RRPF Is NOT

*   **Not an agent framework**: RRPF handles data state and fulfillment. It does not manage loops, planning, or agency.
*   **Not a database**: RRPF is a protocol layer that sits *above* your data sources.
*   **Not an LLM wrapper**: RRPF is agnostic to how the data is consumed. It provides the ground truth; it does not perform the inference.
*   **Not a reasoning engine**: It provides the *context* for reasoning, but does not perform the reasoning itself.

## Core Concepts

### RRPRequest
An immutable object defining the exact scope of data required. It includes the intent, temporal constraints (`as_of`), and strict limits on row counts and group complexity.

### FulfillmentEngine
A pluggable backend responsible for resolving an `RRPRequest` into data. Engines can be backed by anything: in-memory dictionaries, SQL databases, or remote APIs. The engine is responsible for fetching data; the protocol is responsible for validating and hashing it.

### RRPResponse
The result of a fulfillment cycle. It contains the requested data, execution statistics, and a provenance object.

### Digest & Provenance
Every response includes a `provenance` section with an `inputs_digest`. This SHA-256 hash uniquely identifies the request configuration and the resulting data state. If the digest matches, the context is guaranteed to be identical.

### Replay
Because the protocol is deterministic and digest-addressed, any past interaction can be replayed from storage without re-executing the fulfillment engine, guaranteeing that the exact same state is provided to the consumer.

## Minimal Example

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

# 3. Access the deterministic digest
if result.response.ok:
    print(f"Inputs Digest: {result.response.provenance.inputs_digest}")
```

## Guarantees

### Determinism
The protocol enforces canonical JSON serialization and stable sorting for all inputs. Two requests with the same semantic content will always generate the same hash, regardless of key order or formatting.

### Bounded Scope
Constraints are first-class citizens. Requests that exceed defined limits for rows, groups, or complexity are rejected at the protocol level, preventing resource exhaustion.

### Immutable Replay
By storing the `RRPResponse` keyed by its `inputs_digest`, systems can retrieve the exact historical state without re-querying the underlying data sources.

### Engine Independence
The protocol imposes no requirements on the underlying storage technology. A request can be fulfilled by an in-memory mock for testing and a distributed data warehouse for production, with no changes to the consumer logic.

## Stability & Versioning

RRPF follows semantic versioning for the Python library, but the **Protocol Version** (`rrp_version`) is distinct.

*   **Library Version** (e.g., `0.1.0`): Refers to the Python package features and API.
*   **Protocol Version** (e.g., `1.0`): Refers to the wire format and hashing rules.

We guarantee backward compatibility for the protocol definition. A request created with `rrp_version="1.0"` will always be valid and will always produce the same hash in any future version of the library that supports protocol 1.0.

## Documentation

*   [Quickstart Guide](docs/quickstart.md)
*   [Engine Implementation Guide](docs/engines.md)
*   [Versioning Policy](VERSIONING.md)
*   [Changelog](CHANGELOG.md)
