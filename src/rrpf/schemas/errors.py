from dataclasses import dataclass


@dataclass(frozen=True)
class RRPError:
    code: str
    message: str
    section: str | None
