import copy

from rrpf.schemas.common import Digest
from rrpf.schemas.response import RRPResponse


class MemoryPayloadStore:
    """
    Reference in-memory implementation of PayloadStore.
    """

    def __init__(self) -> None:
        self._store: dict[Digest, RRPResponse] = {}

    def store(self, *, digest: Digest, response: RRPResponse) -> None:
        """
        Persist the response in memory.
        If already stored, it overwrites (idempotent for identical payloads).
        """
        # In a real immutable store, we might check if existing content matches.
        # For this reference, last-write-wins is acceptable as long as
        # the digest assumption holds (same digest = same content).
        self._store[digest] = response

    def load(self, *, digest: Digest) -> RRPResponse:
        """
        Load a previously stored response.
        Returns a deep copy to prevent mutation of the store.
        """
        if digest not in self._store:
            raise KeyError(f"Payload not found: {digest}")

        # Return a copy to simulate loading from disk (new object)
        return copy.deepcopy(self._store[digest])
