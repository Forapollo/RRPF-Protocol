from dataclasses import FrozenInstanceError

import pytest

from rrpf.annotations import (
    Capability,
    CapabilityRegistry,
    event,
    inspect_engine_capabilities,
    table,
)


def test_capability_immutability() -> None:
    cap = Capability(kind="table", name="t1", schema={}, max_items=10)
    with pytest.raises(FrozenInstanceError):
        cap.name = "t2"  # type: ignore[misc]

def test_table_decorator() -> None:
    @table(name="users", schema={"fields": ["id"]}, max_rows=100, description="Users table")
    def get_users() -> str:
        return "original_return"

    # Mypy doesn't know about dynamic attributes
    cap = get_users.__rrpf_capability__  # type: ignore[attr-defined]
    assert isinstance(cap, Capability)
    assert cap.kind == "table"
    assert cap.name == "users"
    assert cap.max_items == 100
    assert cap.description == "Users table"

    # Verify function is not wrapped
    assert get_users() == "original_return"

def test_event_decorator() -> None:
    @event(name="logins", schema={"fields": ["ts"]}, max_events=50)
    def get_logins() -> None:
        pass

    cap = get_logins.__rrpf_capability__  # type: ignore[attr-defined]
    assert cap.kind == "event"
    assert cap.name == "logins"
    assert cap.max_items == 50  # mapped from max_events

def test_registry_collection() -> None:
    class MyEngine:
        @table(name="t1", schema={}, max_rows=10)
        def t1(self) -> None: pass

        @event(name="e1", schema={}, max_events=5)
        def e1(self) -> None: pass

        def plain(self) -> None: pass

    engine = MyEngine()
    registry = CapabilityRegistry.from_object(engine)

    assert "t1" in registry.tables
    assert registry.tables["t1"].max_items == 10
    assert "e1" in registry.events
    assert registry.events["e1"].max_items == 5
    assert len(registry.tables) == 1
    assert len(registry.events) == 1

def test_registry_duplicates() -> None:
    class BadEngine:
        @table(name="t1", schema={}, max_rows=10)
        def method1(self) -> None: pass

        @table(name="t1", schema={}, max_rows=20)
        def method2(self) -> None: pass

    with pytest.raises(ValueError, match="Duplicate table capability name: t1"):
        CapabilityRegistry.from_object(BadEngine())

def test_inspect_helper_explicit() -> None:
    registry = CapabilityRegistry(tables={}, events={})
    class ExplicitEngine:
        capabilities = registry

    assert inspect_engine_capabilities(ExplicitEngine()) is registry

def test_inspect_helper_implicit() -> None:
    class ImplicitEngine:
        @table(name="t1", schema={}, max_rows=1)
        def t1(self) -> None: pass

    reg = inspect_engine_capabilities(ImplicitEngine())
    assert reg is not None
    assert "t1" in reg.tables

def test_inspect_helper_none() -> None:
    assert inspect_engine_capabilities(None) is None

def test_decorator_validation() -> None:
    with pytest.raises(ValueError, match="Table name cannot be empty"):
        @table(name="", schema={}, max_rows=1)
        def f() -> None: pass

    with pytest.raises(ValueError, match="max_rows must be positive"):
        @table(name="t", schema={}, max_rows=0)
        def f2() -> None: pass

    with pytest.raises(ValueError, match="max_events must be positive"):
        @event(name="e", schema={}, max_events=0)
        def f3() -> None: pass
