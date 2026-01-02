# Fulfillment Engines

The RRPF protocol allows pluggable execution backends called **Fulfillment Engines**. An engine is responsible for retrieving the requested data and returning it in a standardized format.

## Engine Contract

To implement an engine, you must satisfy the `FulfillmentEngine` protocol:

```python
class FulfillmentEngine(Protocol):
    def fulfill(self, request: RRPRequest) -> FulfillmentResult:
        ...
```

The `fulfill` method receives a fully validated `RRPRequest` and returns a `FulfillmentResult` containing:
1. `data`: The actual data rows for each requested section.
2. `query_stats`: Statistics about the execution (rows scanned, groups, etc.).

## Section Naming Rules

Engines must return data keyed by strict section names:

- **Tables**: `table:{table_name}`
  - Example: `table:users`
- **Events**: `event:{types}` where `types` is `+`-joined sorted event types.
  - Example: `event:click+view`

## QueryStats

`QueryStats` provides visibility into the "cost" or weight of a query section.

- `rows`: The number of rows returned in the result.
- `groups`: The number of groups (if aggregation was used) or 1 for flat queries.

## Requirements

### Engines MUST:
- Return `FulfillmentResult` (or an object adhering to the protocol).
- Use correct section keys.
- Respect `limit` specified in the request (return $\le$ limit rows).
- Be deterministic where possible (e.g., apply stable sorting).

### Engines MUST NOT:
- Raise exceptions for expected data retrieval issues (return empty or omit section instead).
- Modify the request object.
- Return more rows than requested.

## Common Mistakes

1. **Incorrect Section Keys**: Returning `users` instead of `table:users`.
2. **Ignoring Limits**: Returning all 1000 rows when `limit=10`.
3. **Unstable Ordering**: Returning rows in random order, which breaks digest verification.
4. **Crashing on Missing Tables**: Engines should omit the section if a table is missing; the Runner handles partial checks.

## Capability Annotations

Engines can optionally declare their capabilities using decorators. This allows inspection of supported tables and events without executing queries.

See [Engine Capability Annotations](annotations.md) for full documentation and examples.

```python
from rrpf.annotations import table, event


class MyEngine:
    @table(name="users", schema=UserSchema, max_rows=100)
    def get_users(self):
        # RRPF NEVER executes this method
        pass

    @event(name="logins", schema=LoginSchema, max_events=500)
    def get_logins(self):
        pass
```

RRPF provides tools to inspect these capabilities via `rrpf.annotations.inspect_engine_capabilities(engine)`.

**Note**:
*   RRPF **never** executes annotated functions. They serve only as metadata carriers.
*   Annotations are **optional**. Engines can work without them.
