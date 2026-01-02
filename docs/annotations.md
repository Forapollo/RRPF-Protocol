# Engine Capability Annotations

RRPF provides an optional annotation system (`rrpf.annotations`) that allows fulfillment engines to declaratively state their capabilities.

This metadata enables introspection and static analysis of an engine's supported data contracts without executing queries or inspecting the underlying implementation.

## What Annotations Are

*   **Engine-Side Metadata**: A way to tag methods with the RRPF tables or events they fulfill.
*   **Declarative Contracts**: Static definitions of names, schemas, and limits.
*   **Optional**: Engines can function perfectly well without them.

## What Annotations Are NOT

*   **NOT Execution Hooks**: RRPF **never** executes the annotated function. It only reads the decorator metadata.
*   **NOT Database Access**: Annotations do not connect to or validate against a database.
*   **NOT Logic**: They do not change how `run_fulfillment` processes requests or returns data.

## Supported Annotations

### `@table`

Declares support for a specific table.

```python
@rrpf.annotations.table(
    name="users",
    schema=UserSchema,
    max_rows=100,
    description="User profiles"
)
def get_users(self): ...
```

*   `name`: The RRPF table name (e.g., `users` maps to section `table:users`).
*   `schema`: An arbitrary schema object (e.g., Pydantic model, dict, or string) describing the row structure.
*   `max_rows`: The hard limit on rows this capability supports per request.
*   `description`: Optional human-readable documentation.

### `@event`

Declares support for a specific event stream.

```python
@rrpf.annotations.event(
    name="logins",
    schema=LoginSchema,
    max_events=500,
    description="Login attempts"
)
def get_logins(self): ...
```

*   `name`: The RRPF event name.
*   `max_events`: Maps to the capability's `max_items`.

## Complete Example

Here is a realistic example of an annotated engine. Note that the method bodies are empty or contain implementation details that RRPF ignores.

```python
from rrpf.annotations import table, event, inspect_engine_capabilities

# Placeholder schemas
class UserSchema: pass
class OrderSchema: pass

class MyStoreEngine:
    """A sample fulfillment engine with declared capabilities."""

    @table(name="users", schema=UserSchema, max_rows=100)
    def fetch_users(self):
        # Implementation details (SQL, API calls) go here.
        # RRPF ignores this body during introspection.
        pass

    @table(name="orders", schema=OrderSchema, max_rows=50)
    def fetch_orders(self):
        pass

    @event(name="view_item", schema={}, max_events=1000)
    def fetch_views(self):
        pass

# --- Introspection ---

engine = MyStoreEngine()
registry = inspect_engine_capabilities(engine)

if registry:
    print("Engine Capabilities:")
    for name, cap in registry.tables.items():
        print(f"  Table: {name} (Limit: {cap.max_items})")
    
    for name, cap in registry.events.items():
        print(f"  Event: {name} (Limit: {cap.max_items})")
```

## How RRPF Uses Annotations

### Current State (Introspection Only)
As of v0.2.0, annotations are purely informational. RRPF uses them to:
1.  Populate the `CapabilityRegistry` via `inspect_engine_capabilities`.
2.  Allow developers to inspect what an engine supports at runtime.

### Future Enforcement (Deferred)
In future versions, RRPF may offer an *opt-in* mode to enforce that requested tables exist in the engine's capability registry before attempting fulfillment. This is currently deferred to ensure maximum compatibility and zero overhead for existing engines.
