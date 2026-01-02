
from rrpf.schemas import RRPRequest
from rrpf.schemas.as_of import AsOfMode
from rrpf.validation.errors import ValidationError


def validate_version(request: RRPRequest) -> list[ValidationError]:
    if request.rrp_version != "1.0":
        return [
            ValidationError(
                code="invalid_version",
                message=f"rrp_version must be '1.0', got '{request.rrp_version}'",
                path="rrp_version",
            )
        ]
    return []


def validate_as_of(request: RRPRequest) -> list[ValidationError]:
    errors = []
    if request.as_of.mode == AsOfMode.TIMESTAMP:
        if request.as_of.timestamp is None:
            errors.append(
                ValidationError(
                    code="missing_timestamp",
                    message="as_of mode TIMESTAMP requires a timestamp",
                    path="as_of.timestamp",
                )
            )
    elif request.as_of.mode == AsOfMode.LATEST and request.as_of.timestamp is not None:
        errors.append(
            ValidationError(
                code="unexpected_timestamp",
                message="as_of mode LATEST requires timestamp to be None",
                path="as_of.timestamp",
            )
        )
    return errors


def validate_constraints(request: RRPRequest) -> list[ValidationError]:
    errors = []
    if request.constraints.max_total_rows <= 0:
        errors.append(
            ValidationError(
                code="invalid_max_total_rows",
                message="max_total_rows must be > 0",
                path="constraints.max_total_rows",
            )
        )
    if request.constraints.max_groups <= 0:
        errors.append(
            ValidationError(
                code="invalid_max_groups",
                message="max_groups must be > 0",
                path="constraints.max_groups",
            )
        )
    return errors


def validate_tables(request: RRPRequest) -> list[ValidationError]:
    errors = []
    for i, table in enumerate(request.data.tables):
        path_prefix = f"data.tables[{i}]"
        if not table.table:
            errors.append(
                ValidationError(
                    code="empty_table_name",
                    message="table name must be non-empty",
                    path=f"{path_prefix}.table",
                )
            )
        if not table.fields:
            errors.append(
                ValidationError(
                    code="empty_fields",
                    message="fields list must not be empty",
                    path=f"{path_prefix}.fields",
                )
            )
        if table.limit <= 0:
            errors.append(
                ValidationError(
                    code="invalid_limit",
                    message="limit must be > 0",
                    path=f"{path_prefix}.limit",
                )
            )
    return errors


def validate_events(request: RRPRequest) -> list[ValidationError]:
    errors = []
    for i, event in enumerate(request.data.events):
        path_prefix = f"data.events[{i}]"
        if not event.types:
            errors.append(
                ValidationError(
                    code="empty_types",
                    message="types list must not be empty",
                    path=f"{path_prefix}.types",
                )
            )
        if not event.fields:
            errors.append(
                ValidationError(
                    code="empty_fields",
                    message="fields list must not be empty",
                    path=f"{path_prefix}.fields",
                )
            )
        if event.limit <= 0:
            errors.append(
                ValidationError(
                    code="invalid_limit",
                    message="limit must be > 0",
                    path=f"{path_prefix}.limit",
                )
            )
    return errors


def validate_groups_count(request: RRPRequest) -> list[ValidationError]:
    total_groups = len(request.data.tables) + len(request.data.events)
    if total_groups > request.constraints.max_groups:
        return [
            ValidationError(
                code="max_groups_exceeded",
                message=f"Total tables+events ({total_groups}) exceeds max_groups ({request.constraints.max_groups})",
                path="data",
            )
        ]
    return []


def validate_no_empty_request(request: RRPRequest) -> list[ValidationError]:
    if not request.data.tables and not request.data.events:
        return [
            ValidationError(
                code="empty_request",
                message="At least one table or event must be requested",
                path="data",
            )
        ]
    return []
