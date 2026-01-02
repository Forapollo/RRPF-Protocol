from dataclasses import dataclass


@dataclass(frozen=True)
class Constraints:
    max_total_rows: int
    max_groups: int
    fail_on_partial: bool
