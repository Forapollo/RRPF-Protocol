import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

from rrpf import run_and_store
from rrpf.examples import InMemoryEngine
from rrpf.schemas.as_of import AsOf, AsOfMode
from rrpf.schemas.common import CorrelationID, RequestID
from rrpf.schemas.constraints import Constraints
from rrpf.schemas.data_requests import DataRequests, TableRequest
from rrpf.schemas.intent import Intent, IntentMode
from rrpf.schemas.request import RRPRequest
from rrpf.storage import FilesystemPayloadStore, MemoryPayloadStore, replay_from_store


def _create_request() -> RRPRequest:
    return RRPRequest(
        rrp_version="1.0",
        request_id=cast(RequestID, "req-storage"),
        correlation_id=cast(CorrelationID, "corr-storage"),
        requested_at=datetime.now(UTC),
        intent=Intent(name="test_storage", mode=IntentMode.SNAPSHOT),
        as_of=AsOf(mode=AsOfMode.LATEST, timestamp=None),
        constraints=Constraints(max_total_rows=100, max_groups=10, fail_on_partial=True),
        data=DataRequests(
            tables=[TableRequest(table="t1", fields=["id"], limit=5, derived=None)],
            events=[],
        ),
    )


def test_memory_store_roundtrip() -> None:
    req = _create_request()
    engine = InMemoryEngine()
    store = MemoryPayloadStore()

    # 1. Run and Store
    result = run_and_store(request=req, engine=engine, store=store)

    assert result.response.ok is True
    digest = result.digest
    assert digest

    # 2. Replay
    replayed = replay_from_store(digest=digest, store=store)

    # 3. Assert Equality
    # Can't compare full objects easily due to internal dataclasses,
    # but specific fields and digest should match.
    assert replayed.request_id == result.response.request_id
    assert replayed.provenance.inputs_digest == digest
    assert replayed.data == result.response.data

    # 4. Immutability Check (Load returns copy)
    replayed_2 = replay_from_store(digest=digest, store=store)
    assert replayed is not replayed_2


def test_filesystem_store_roundtrip() -> None:
    req = _create_request()
    engine = InMemoryEngine()

    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemPayloadStore(root=tmp_dir)

        # 1. Run and Store
        result = run_and_store(request=req, engine=engine, store=store)
        digest = result.digest

        # Verify file exists
        expected_path = Path(tmp_dir) / f"{digest}.json"
        assert expected_path.exists()

        # 2. Replay
        replayed = replay_from_store(digest=digest, store=store)

        assert replayed.provenance.inputs_digest == digest
        assert replayed.data == result.response.data

        # 3. Verify Datetime Roundtrip
        # ISO format conversion should preserve time (allowing for precision diffs if any,
        # but Python ISO format usually preserves microseconds)
        assert replayed.provenance.fulfilled_at == result.response.provenance.fulfilled_at


def test_replay_immutability() -> None:
    req = _create_request()
    engine = InMemoryEngine()
    store = MemoryPayloadStore()

    result = run_and_store(request=req, engine=engine, store=store)
    digest = result.digest

    replayed = replay_from_store(digest=digest, store=store)

    # Modifying replayed object (if it were mutable) should not affect store
    # Since RRPResponse is frozen, we can't easily mutate it directly.
    # But if we could, the next load should still be pristine.

    # Let's try to mutate the underlying dict of data if possible,
    # though Mapping is read-only.
    # We can try to hack it or just rely on "load returns deepcopy".

    # In MemoryPayloadStore, we explicitly do deepcopy.
    # In FilesystemPayloadStore, we deserialize from disk every time (new object).

    replayed_2 = replay_from_store(digest=digest, store=store)
    assert replayed is not replayed_2
    assert replayed == replayed_2


def test_filesystem_digest_mismatch() -> None:
    req = _create_request()
    engine = InMemoryEngine()

    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemPayloadStore(root=tmp_dir)
        result = run_and_store(request=req, engine=engine, store=store)
        digest = result.digest

        # Corrupt the file content's digest field but keep filename
        path = Path(tmp_dir) / f"{digest}.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Tamper with inputs_digest in the file
        data["provenance"]["inputs_digest"] = "bad_digest"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Load should raise AssertionError
        with pytest.raises(AssertionError, match="Integrity check failed"):
            replay_from_store(digest=digest, store=store)
