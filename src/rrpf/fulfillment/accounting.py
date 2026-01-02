from rrpf.schemas.constraints import Constraints


def check_row_constraints(
    *,
    requested_rows: int,
    constraints: Constraints,
) -> bool:
    """
    Return True if requested rows are within constraints.
    """
    return requested_rows <= constraints.max_total_rows
