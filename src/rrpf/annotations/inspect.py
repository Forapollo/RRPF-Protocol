from typing import Any

from rrpf.annotations.registry import CapabilityRegistry


def inspect_engine_capabilities(engine: Any) -> CapabilityRegistry | None:
    """
    Inspect an engine instance to discover its capabilities.

    1. Checks for an explicit `capabilities` attribute.
    2. Falls back to inspecting methods decorated with @table/@event.
    3. Returns None if engine is None.
    """
    if engine is None:
        return None

    # 1. Explicit attribute
    # We use getattr with a default to avoid raising AttributeError,
    # though hasattr check is also fine.
    capabilities = getattr(engine, "capabilities", None)
    if capabilities is not None:
        # We assume it's a valid CapabilityRegistry or compatible if present
        return capabilities  # type: ignore[no-any-return]

    # 2. Introspection
    # This returns a registry (possibly empty)
    return CapabilityRegistry.from_object(engine)
