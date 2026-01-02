import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from rrpf.hashing.canonical_json import to_canonical_json
from rrpf.schemas.common import Digest, RequestID
from rrpf.schemas.errors import RRPError
from rrpf.schemas.provenance import Provenance, QueryStats
from rrpf.schemas.response import RRPResponse


class FilesystemPayloadStore:
    """
    Filesystem-backed implementation of PayloadStore.
    Persists responses as digest-addressed JSON files.
    """

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def store(self, *, digest: Digest, response: RRPResponse) -> None:
        """
        Persist the response to a file named <digest>.json.
        Writes atomically via a temporary file.
        """
        path = self.root / f"{digest}.json"

        # Serialize to dict first
        data = _serialize_response(response)
        # Use canonical JSON for deterministic formatting
        content = to_canonical_json(data)

        # Atomic write
        with tempfile.NamedTemporaryFile(
            mode="w", dir=str(self.root), delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        shutil.move(str(tmp_path), str(path))

    def load(self, *, digest: Digest) -> RRPResponse:
        """
        Load response from <digest>.json.
        """
        path = self.root / f"{digest}.json"
        if not path.exists():
            raise KeyError(f"Payload not found: {digest}")

        with path.open("r", encoding="utf-8") as f:
            content = f.read()

        data = json.loads(content)
        response = _deserialize_response(data)

        # Verify integrity
        if response.provenance.inputs_digest != digest:
            # If the stored file corresponds to a different digest than requested,
            # that's a serious integrity issue or misuse.
            # However, the user request says "inputs_digest must match filename digest".
            # Note: The digest passed to store/load is the request/inputs digest,
            # which matches response.provenance.inputs_digest.
            raise AssertionError(
                f"Integrity check failed: stored digest {response.provenance.inputs_digest} "
                f"does not match requested digest {digest}"
            )

        return response


def _serialize_response(resp: RRPResponse) -> dict[str, Any]:
    """Helper to serialize RRPResponse to a dict."""
    return {
        "ok": resp.ok,
        "request_id": resp.request_id,
        "as_of": resp.as_of,
        "partial": resp.partial,
        "data": dict(resp.data),
        "errors": [
            {"code": e.code, "message": e.message, "section": e.section}
            for e in resp.errors
        ],
        "provenance": {
            "fulfilled_at": resp.provenance.fulfilled_at.isoformat().replace("+00:00", "Z"),
            "inputs_digest": resp.provenance.inputs_digest,
            "query_stats": {
                k: {"rows": v.rows, "groups": v.groups}
                for k, v in resp.provenance.query_stats.items()
            },
        },
    }


def _deserialize_response(data: dict[str, Any]) -> RRPResponse:
    """Helper to deserialize dict to RRPResponse."""
    # Provenance
    prov_data = data["provenance"]
    stats: dict[str, QueryStats] = {}
    for k, v in prov_data["query_stats"].items():
        stats[k] = QueryStats(rows=v["rows"], groups=v["groups"])

    # Handle timestamp: ISO format potentially with Z
    ts_str = prov_data["fulfilled_at"]
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    fulfilled_at = datetime.fromisoformat(ts_str)

    provenance = Provenance(
        fulfilled_at=fulfilled_at,
        inputs_digest=cast(Digest, prov_data["inputs_digest"]),
        query_stats=stats,
    )

    # Errors
    errors = [
        RRPError(code=e["code"], message=e["message"], section=e["section"])
        for e in data["errors"]
    ]

    return RRPResponse(
        ok=data["ok"],
        request_id=cast(RequestID, data["request_id"]),
        as_of=data["as_of"],
        partial=data["partial"],
        data=data["data"],
        errors=errors,
        provenance=provenance,
    )
