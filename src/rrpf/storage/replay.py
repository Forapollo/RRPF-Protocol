from rrpf.schemas.common import Digest
from rrpf.schemas.response import RRPResponse
from rrpf.storage.payload_store import PayloadStore


def replay_from_store(
    *,
    digest: Digest,
    store: PayloadStore,
) -> RRPResponse:
    """
    Replay a fulfilled RRPF payload without re-executing fulfillment.
    """
    return store.load(digest=digest)
