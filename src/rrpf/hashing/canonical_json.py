import json
from collections.abc import Mapping
from typing import Any


def to_canonical_json(data: Mapping[str, Any]) -> str:
    """
    Serialize canonical mapping to canonical JSON string.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
