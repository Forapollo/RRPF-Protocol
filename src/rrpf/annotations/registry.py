from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from rrpf.annotations.base import Capability


@dataclass(frozen=True)
class CapabilityRegistry:
    tables: Mapping[str, Capability]
    events: Mapping[str, Capability]

    @classmethod
    def from_object(cls, obj: Any) -> "CapabilityRegistry":
        tables: dict[str, Capability] = {}
        events: dict[str, Capability] = {}

        # Scan all attributes of the object (including methods)
        # We use dir() to get all attributes, including those from class
        for attr_name in dir(obj):
            try:
                attr = getattr(obj, attr_name)
            except Exception:
                # Some attributes might not be accessible or raise errors on access
                continue

            capability = getattr(attr, "__rrpf_capability__", None)
            if isinstance(capability, Capability):
                if capability.kind == "table":
                    if capability.name in tables:
                        raise ValueError(f"Duplicate table capability name: {capability.name}")
                    tables[capability.name] = capability
                elif capability.kind == "event":
                    if capability.name in events:
                        raise ValueError(f"Duplicate event capability name: {capability.name}")
                    events[capability.name] = capability

        return cls(tables=tables, events=events)
