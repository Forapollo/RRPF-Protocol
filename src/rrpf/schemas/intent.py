from dataclasses import dataclass
from enum import Enum


class IntentMode(str, Enum):
    SNAPSHOT = "snapshot"
    ANALYSIS = "analysis"
    AUDIT = "audit"

@dataclass(frozen=True)
class Intent:
    name: str
    mode: IntentMode
