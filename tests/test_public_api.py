import rrpf


def test_public_api_surface() -> None:
    """
    Ensure rrpf.__all__ exposes only the intended public API.
    This prevents accidental leakage of internal modules.
    """
    expected = {
        # Schemas
        "AsOf",
        "Constraints",
        "DataRequests",
        "EventRequest",
        "Intent",
        "Provenance",
        "RRPError",
        "RRPRequest",
        "RRPResponse",
        "TableRequest",

        # Validation
        "validate_request",
        "ValidationError",

        # Hashing / Normalization
        "canonicalize_request",
        "to_canonical_json",
        "compute_digest",

        # Fulfillment
        "FulfillmentEngine",
        "run_fulfillment",
        "RunResult",
        "run_and_store",

        # Storage
        "PayloadStore",
        "MemoryPayloadStore",
        "FilesystemPayloadStore",
        "replay_from_store",

        # Version
        "__version__",
    }

    actual = set(rrpf.__all__)
    assert actual == expected

    # Also verify that no other names are exported via module introspection
    # (though __all__ controls "from rrpf import *", direct access "rrpf.foo" is controlled by what's bound)
    # We mainly care that we didn't miss adding something to __all__ that IS available,
    # or added something to __all__ that doesn't exist.

    for name in expected:
        assert hasattr(rrpf, name), f"Public API {name} missing from module"


def test_no_internal_modules_leaked() -> None:
    """
    Verify we aren't re-exporting internal submodules directly in top-level.
    """
    # These should NOT be in rrpf.__all__ or directly importable as `from rrpf import x`
    # unless explicitly exposed.
    forbidden = [
        "hashing",
        "normalization",
        "validation",
        "fulfillment",
        "storage",
        "schemas"
    ]

    for module_name in forbidden:
        assert module_name not in rrpf.__all__
