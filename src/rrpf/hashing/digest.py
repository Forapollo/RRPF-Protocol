import hashlib
from typing import cast

from rrpf.schemas.common import Digest


def compute_digest(canonical_json: str) -> Digest:
    """
    Compute SHA-256 digest of canonical JSON.
    """
    digest_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return cast(Digest, digest_hash)
