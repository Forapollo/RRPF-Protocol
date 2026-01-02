import rrpf


def test_package_version() -> None:
    """Assert package version is exactly 0.2.0"""
    assert rrpf.__version__ == "0.2.0"


def test_protocol_version_lock() -> None:
    """
    Assert that the protocol law requires rrp_version="1.0".
    Even though the package is 0.1.0, the protocol spec is 1.0.
    """
    # Create a dummy request with version 1.0
    # We can reuse the validator to check this logic

    # We don't need a full valid request, just enough to check the version logic
    # But validate_request expects a full structure.
    # Let's rely on the fact that we have a version constant or we can check validation error on bad version.

    # Check validator logic by passing a mock-like object or just creating a minimal request
    # Since we can't easily partial-construct frozen dataclasses, let's look at the failure case.

    # This relies on the fact that our validation rules enforce "1.0"
    from rrpf.validation.rules import validate_version

    # Mock minimal object structure for validation
    class MockRequest:
        def __init__(self, version: str) -> None:
            self.rrp_version = version

    assert validate_version(MockRequest("1.0")) == [] # type: ignore
    assert validate_version(MockRequest("0.1.0")) != [] # type: ignore
    assert validate_version(MockRequest("2.0")) != [] # type: ignore
