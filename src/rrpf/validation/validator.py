
from rrpf.schemas.request import RRPRequest
from rrpf.validation.errors import ValidationError
from rrpf.validation.rules import (
    validate_as_of,
    validate_constraints,
    validate_events,
    validate_groups_count,
    validate_no_empty_request,
    validate_tables,
    validate_version,
)


def validate_request(request: RRPRequest) -> list[ValidationError]:
    """
    Run all protocol validation rules.
    """
    errors: list[ValidationError] = []

    # Aggregate errors from all rules
    errors.extend(validate_version(request))
    errors.extend(validate_as_of(request))
    errors.extend(validate_constraints(request))
    errors.extend(validate_tables(request))
    errors.extend(validate_events(request))
    errors.extend(validate_groups_count(request))
    errors.extend(validate_no_empty_request(request))

    return errors
