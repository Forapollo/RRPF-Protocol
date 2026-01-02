from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str
    path: str | None
