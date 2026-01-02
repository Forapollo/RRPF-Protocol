from typing import Protocol

from rrpf.schemas.common import Digest
from rrpf.schemas.response import RRPResponse


class PayloadStore(Protocol):
    """
    Protocol for persisting and retrieving fulfilled RRPF responses.
    Storage is digest-addressed and immutable-by-convention.
    """

    def store(self, *, digest: Digest, response: RRPResponse) -> None:
        """
        Persist the response verbatim.
        Must be idempotent.
        """
        ...

    def load(self, *, digest: Digest) -> RRPResponse:
        """
        Load a previously stored response.
        Must raise KeyError if missing.
        """
        ...
