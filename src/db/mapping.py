"""Type mapping utilities for crispsec project."""

from .types import ALL_TYPES

_TYPE_TO_PREFIX: dict[str, str] = {
    "draft": "DRAFT",
    "requirement": "REQ",
    "user-story": "US",
    "business-concept": "BC",
    "entity": "ENT",
    "interface": "API",
    "event": "EVT",
    "error": "ERR",
    "process": "PROC",
    "orchestration": "ORCH",
    "reaction": "SUB",
    "schedule": "SCH",
    "repository": "REPO",
    "code-ref": "CREF",
    "incident": "INC",
    "runbook": "RB",
    "playbook": "PB",
    "constraint": "CON",
    "metric": "MET",
    "role": "ROLE",
    "permission": "PERM",
    "dependency": "DEP",
    "module": "MOD",
    "environment": "ENV",
    "pipeline": "PIPE",
    "configuration": "CONF",
    "config-set": "CSET",
    "confidential_value": "CONFIDENTIAL",
    "acceptance-test": "AT",
    "scenario-test": "ST",
    "integration-test": "IT",
    "contract-test": "CT",
    "transition-test": "TT",
    "benchmark": "BM",
}

PREFIX_TO_TYPE = {v: k for k, v in _TYPE_TO_PREFIX.items()}
_PREFIX_TO_TYPE = PREFIX_TO_TYPE


def type_to_prefix(type_name: str) -> str:
    """Convert a type name to its prefix."""
    if type_name not in _TYPE_TO_PREFIX:
        msg = f"Unknown type: {type_name}"
        raise ValueError(msg)
    return _TYPE_TO_PREFIX[type_name]


def prefix_to_type(prefix: str) -> str:
    """Convert a prefix to its type name."""
    if prefix not in PREFIX_TO_TYPE:
        msg = f"Unknown prefix: {prefix}"
        raise ValueError(msg)
    return PREFIX_TO_TYPE[prefix]


def generate_id(type_name: str, auto_id: int) -> str:
    """Generate an ID from a type and auto-increment number."""
    prefix = type_to_prefix(type_name)
    return f"{prefix}-{auto_id}"


def parse_id(record_id: str) -> tuple[str, int]:
    """Parse an ID into its type and number."""
    prefix, num_str = record_id.rsplit("-", 1)
    type_ = prefix_to_type(prefix)
    return type_, int(num_str)


def is_valid_type(type_name: str) -> bool:
    """Check if a type name is valid."""
    return type_name in _TYPE_TO_PREFIX


def get_all_types() -> tuple[str, ...]:
    """Get all valid type names."""
    return ALL_TYPES
