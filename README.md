# RRPF Protocol

## What RRPF Is

RRPF is a deterministic protocol for explicitly scoped data fulfillment and immutable reasoning payloads.

## What RRPF Is NOT

*   Not a framework
*   Not an agent system
*   Not a database
*   Not a reasoning engine

## Guarantees

*   Deterministic canonicalization
*   Cryptographic request digests
*   Explicit constraints
*   Immutable replay
*   Engine-agnostic fulfillment

## Quick Example

```python
from rrpf import RRPRequest, run_fulfillment
from rrpf.examples import InMemoryEngine

# 1. Instantiate engine
engine = InMemoryEngine()

# 2. Run fulfillment (assumes valid request object)
result = run_fulfillment(request, engine)

# 3. Inspect results
if result.response.ok:
    print(f"Fulfilled: {result.digest}")
```

## Stability

*   **v0.1.0** frozen
*   Backward compatibility promise for **0.1.x**
