from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AsOfMode(str, Enum):
    LATEST = "latest"
    TIMESTAMP = "timestamp"

@dataclass(frozen=True)
class AsOf:
    mode: AsOfMode
    timestamp: datetime | None
