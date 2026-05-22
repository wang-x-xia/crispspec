"""YAML schema type management.

Provides the :class:`Schema` class to create, check, and verify type
definitions based on the ``__self`` / ``__typedefs`` structure.

Type definitions are persisted via the ``Storage`` interface from ``src.db``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import yaml

from src.db.types import type_def

if TYPE_CHECKING:
    from src.db.interface import Storage

_EXPECTED_PARTS = 3
_MIN_LOCAL_REF_LEN = 2
_RESERVED_KEYS = frozenset({"__self", "__typedefs"})

BUILTIN_TYPES = frozenset({"string", "number", "bool"})


# ---------------------------------------------------------------------------
# Type classification
# ---------------------------------------------------------------------------


class TypeKind(Enum):
    """Classification of field types.

    * ``PRIMITIVE``      - ``string``, ``number``, ``bool``
    * ``COMPOSITE``      - ``object`` / ``array``
    * ``INLINE_LINK``    - ``@.Name`` (current file ``__typedefs``)
    * ``EXTERNAL_LINK``  - ``@TYPE-{ID}`` or ``@TYPE-{ID}.{name}``
    """

    PRIMITIVE = "primitive"
    COMPOSITE = "composite"
    INLINE_LINK = "inline-link"
    EXTERNAL_LINK = "external-link"


def classify_type(type_str: str) -> TypeKind | None:
    """Classify a raw type string into a :class:`TypeKind`.

    Returns ``None`` if *type_str* is not recognised.
    """
    if type_str in BUILTIN_TYPES:
        return TypeKind.PRIMITIVE
    if type_str in {"object", "array"}:
        return TypeKind.COMPOSITE
    if type_str.startswith("@."):
        return TypeKind.INLINE_LINK
    if type_str.startswith("@TYPE-"):
        return TypeKind.EXTERNAL_LINK
    return None


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FieldDef:
    """A parsed field definition."""

    type: str
    parameters: list[str] = field(default_factory=list)
    description: str = ""
    children: dict[str, FieldDef] | None = None
    items: FieldDef | None = None

    @property
    def kind(self) -> TypeKind | None:
        """Derived classification of :attr:`type`."""
        return classify_type(self.type)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_field(raw: str) -> FieldDef:
    """Parse ``type;params;description`` into a :class:`FieldDef`.

    Raises:
        ValueError: If *raw* does not contain exactly two semicolons.

    """
    parts = raw.split(";", 2)
    if len(parts) != _EXPECTED_PARTS:
        msg = f"Invalid field definition (expected 'type;params;desc'): {raw}"
        raise ValueError(msg)

    type_str = parts[0].strip()
    params_str = parts[1].strip()
    desc = parts[2].strip()

    parameters = (
        [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
    )
    return FieldDef(type=type_str, parameters=parameters, description=desc)


def parse_definition(raw: str | dict | list) -> FieldDef:
    """Parse a raw YAML-level value into a :class:`FieldDef`.

    *raw* may be a ``str``, ``dict``, or single-element ``list``.
    """
    if isinstance(raw, str):
        return parse_field(raw)
    if isinstance(raw, dict):
        return FieldDef(type="object", children=_parse_children(raw))
    if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], str):
        return FieldDef(type="array", items=parse_field(raw[0]))
    msg = f"Invalid type definition: {raw}"
    raise ValueError(msg)


def _parse_children(raw_fields: dict) -> dict[str, FieldDef]:
    """Recursively parse a dict of raw child field definitions."""
    result: dict[str, FieldDef] = {}
    for name, value in raw_fields.items():
        result[name] = parse_definition(value)
    return result


# ---------------------------------------------------------------------------
# Top-level structure validation
# ---------------------------------------------------------------------------


def _validate_structure(raw: dict) -> list[str]:
    """Validate the ``__self`` / ``__typedefs`` top-level structure."""
    if "__self" not in raw:
        return ["Missing required key: __self"]
    extra = set(raw) - _RESERVED_KEYS
    if extra:
        return [f"Unexpected top-level keys (only __self and __typedefs allowed): {extra}"]
    return []


# ---------------------------------------------------------------------------
# Definition validation (checks the schema itself, not data)
# ---------------------------------------------------------------------------


def _validate_type_str(type_str: str) -> list[str]:
    """Return errors for an invalid *type_str*."""
    kind = classify_type(type_str)
    if kind is None:
        return [f"Unknown type: {type_str}"]
    if kind in {TypeKind.PRIMITIVE, TypeKind.COMPOSITE}:
        return []
    if kind == TypeKind.INLINE_LINK:
        return (
            [f"Empty local type reference: {type_str}"]
            if len(type_str) <= _MIN_LOCAL_REF_LEN
            else []
        )
    # EXTERNAL_LINK - @TYPE-{ID} or @TYPE-{ID}.{name}, both valid as long as
    # there is an ID part after @TYPE-
    if type_str == "@TYPE-":
        return [f"Empty external type reference: {type_str}"]
    return []


def _validate_field_def(fd: FieldDef) -> list[str]:
    """Return a list of validation errors for *fd*."""
    errors = _validate_type_str(fd.type)
    for param in fd.parameters:
        if not param.startswith("@"):
            errors.append(f"Parameter must start with '@': {param}")
    if fd.children:
        for name, child in fd.children.items():
            errors.extend(f"{name}.{e}" for e in _validate_field_def(child))
    if fd.items:
        errors.extend(f"[].{e}" for e in _validate_field_def(fd.items))
    return errors


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def _field_to_dict(fd: FieldDef) -> dict:
    """Serialize a :class:`FieldDef` into a JSON-friendly dict."""
    d: dict = {
        "type": fd.type,
        "parameters": fd.parameters,
        "description": fd.description,
    }
    if fd.children:
        d["children"] = {k: _field_to_dict(v) for k, v in fd.children.items()}
    if fd.items:
        d["items"] = _field_to_dict(fd.items)
    return d


def _dict_to_field(d: dict) -> FieldDef:
    """Deserialize a dict back into a :class:`FieldDef`."""
    children = (
        {k: _dict_to_field(v) for k, v in d["children"].items()}
        if "children" in d
        else None
    )
    items = _dict_to_field(d["items"]) if "items" in d else None
    return FieldDef(
        type=d["type"],
        parameters=d.get("parameters", []),
        description=d.get("description", ""),
        children=children,
        items=items,
    )


# ---------------------------------------------------------------------------
# Schema class
# ---------------------------------------------------------------------------


class Schema:
    """Manages type definitions backed by a :class:`Storage` instance."""

    def __init__(self, storage: Storage) -> None:
        """Initialize with the given *storage* backend."""
        self._storage = storage

    # -- public API ---------------------------------------------------------

    def create_type(self, raw: dict) -> str:
        """Persist a type YAML (``__self`` + optional ``__typedefs``).

        Args:
            raw: A dict with a required ``__self`` key and an optional
                ``__typedefs`` key.  No other top-level keys are allowed.

        Returns:
            The record ID (``TYPE-...``) assigned by the storage layer.

        Raises:
            ValueError: If the structure or any definition is invalid.

        """
        struct_errors = _validate_structure(raw)
        if struct_errors:
            msg = "Structure errors:\n" + "\n".join(f"  - {e}" for e in struct_errors)
            raise ValueError(msg)

        self_fd = parse_definition(raw["__self"])
        typedefs_fds: dict[str, FieldDef] = {}
        if "__typedefs" in raw:
            for name, value in raw["__typedefs"].items():
                typedefs_fds[name] = parse_definition(value)

        # validate all definitions
        all_errors: list[str] = []
        all_errors.extend(f"__self: {e}" for e in _validate_field_def(self_fd))
        for name, fd in typedefs_fds.items():
            all_errors.extend(
                f"__typedefs.{name}: {e}" for e in _validate_field_def(fd)
            )
        if all_errors:
            msg = "Type definition errors:\n" + "\n".join(
                f"  - {e}" for e in all_errors
            )
            raise ValueError(msg)

        # serialize and persist
        payload: dict = {"__self": _field_to_dict(self_fd)}
        if typedefs_fds:
            payload["__typedefs"] = {
                k: _field_to_dict(v) for k, v in typedefs_fds.items()
            }
        record = self._storage.create(
            type_def,
            yaml.dump(payload, allow_unicode=True, default_flow_style=False),
        )
        return record.id

    def get_type(self, type_id: str) -> dict | None:
        """Look up a type by its record *type_id*.

        Returns:
            The stored dict (``__self`` and optionally ``__typedefs``), or
            ``None`` if not found.

        """
        try:
            record = self._storage.get_by_id(type_id)
        except (ValueError, KeyError):
            return None
        if record is None:
            return None
        return yaml.safe_load(record.data)

    def verify_type(
        self, type_id: str, data: object, *, name: str | None = None,
    ) -> list[str]:
        """Verify *data* against a type stored under *type_id*.

        When *name* is ``None`` (default), validates against ``__self``.
        When *name* is given, validates against the corresponding
        ``__typedefs`` entry.

        Returns:
            A list of error strings; empty means valid.

        """
        td = self.get_type(type_id)
        if td is None:
            return [f"Type '{type_id}' not found"]

        if name is None:
            fd = _dict_to_field(td["__self"])
            return self._check_value(data, fd, type_id)

        typedefs = td.get("__typedefs", {})
        if name not in typedefs:
            return [f"'{name}' not found in {type_id}.__typedefs"]
        fd = _dict_to_field(typedefs[name])
        return self._check_value(data, fd, f"{type_id}.{name}")

    # -- value checking (recursive) -----------------------------------------

    def _check_value(
        self,
        value: object,
        fd: FieldDef,
        path: str,
    ) -> list[str]:
        """Recursively validate *value* against *fd*."""
        if value is None:
            if "@required" in fd.parameters:
                return [f"'{path}' is required"]
            return []

        kind = fd.kind
        errors: list[str] = []

        if kind == TypeKind.PRIMITIVE:
            errors.extend(_check_builtin(value, fd, path))
        elif kind == TypeKind.COMPOSITE:
            errors.extend(self._check_composite(value, fd, path))
        elif kind in {TypeKind.INLINE_LINK, TypeKind.EXTERNAL_LINK}:
            errors.extend(self._check_link(value, fd.type, path))

        if isinstance(value, str):
            errors.extend(_check_pattern(value, fd.parameters, path))

        return errors

    def _check_composite(
        self,
        value: object,
        fd: FieldDef,
        path: str,
    ) -> list[str]:
        """Dispatch to object / array checking."""
        if fd.type == "object" and fd.children:
            return self._check_object(value, fd.children, path)
        if fd.type == "array" and fd.items:
            return self._check_array(value, fd.items, path)
        return []

    def _check_object(
        self,
        value: object,
        children: dict[str, FieldDef],
        path: str,
    ) -> list[str]:
        """Check that *value* is a dict matching *children* field defs."""
        if not isinstance(value, dict):
            return [f"'{path}' must be an object, got {type(value).__name__}"]
        errors: list[str] = []
        for child_name, child_fd in children.items():
            errors.extend(
                self._check_value(value.get(child_name), child_fd, f"{path}.{child_name}"),
            )
        return errors

    def _check_array(
        self,
        value: object,
        items_fd: FieldDef,
        path: str,
    ) -> list[str]:
        """Check that *value* is a list whose items match *items_fd*."""
        if not isinstance(value, list):
            return [f"'{path}' must be an array, got {type(value).__name__}"]
        errors: list[str] = []
        for i, item in enumerate(value):
            errors.extend(self._check_value(item, items_fd, f"{path}[{i}]"))
        return errors

    def _check_link(
        self,
        value: object,
        type_str: str,
        path: str,
    ) -> list[str]:
        """Resolve and validate a type reference."""
        # @.Name - local __typedefs ref (resolved by caller's context, but we
        # don't have the "current type" context here yet; for now treat the
        # same as an external lookup by name within all stored types' typedefs)
        if type_str.startswith("@."):
            ref_name = type_str[2:]
            return self._check_inline_ref(value, ref_name, path)

        # @TYPE-{ID}.{name} - external typedefs entry
        m = re.match(r"@(TYPE-.+)\.(.+)", type_str)
        if m:
            return self._check_external_ref(value, m.group(1), m.group(2), path)

        # @TYPE-{ID} - external __self
        m = re.match(r"@(TYPE-.+)", type_str)
        if m:
            return self._check_external_self(value, m.group(1), path)

        return [f"'{path}': unresolvable type reference: {type_str}"]

    def _check_inline_ref(
        self,
        value: object,
        ref_name: str,
        path: str,
    ) -> list[str]:
        """Resolve ``@.Name`` - search all stored types' ``__typedefs``."""
        for record in self._storage.list_by_type(type_def):
            td = yaml.safe_load(record.data)
            typedefs = td.get("__typedefs", {})
            if ref_name in typedefs:
                fd = _dict_to_field(typedefs[ref_name])
                return self._check_value(value, fd, path)
        return [f"'{path}': referenced type '@.{ref_name}' not found"]

    def _check_external_self(
        self,
        value: object,
        type_id: str,
        path: str,
    ) -> list[str]:
        """Resolve ``@TYPE-{ID}`` - validate against the target's ``__self``."""
        td = self.get_type(type_id)
        if td is None:
            return [f"'{path}': referenced type '{type_id}' not found"]
        fd = _dict_to_field(td["__self"])
        return self._check_value(value, fd, path)

    def _check_external_ref(
        self,
        value: object,
        type_id: str,
        ref_name: str,
        path: str,
    ) -> list[str]:
        """Resolve ``@TYPE-{ID}.{name}`` - target's ``__typedefs`` entry."""
        td = self.get_type(type_id)
        if td is None:
            return [f"'{path}': referenced type '{type_id}' not found"]
        typedefs = td.get("__typedefs", {})
        if ref_name not in typedefs:
            return [f"'{path}': '{ref_name}' not found in {type_id}.__typedefs"]
        fd = _dict_to_field(typedefs[ref_name])
        return self._check_value(value, fd, path)


# ---------------------------------------------------------------------------
# Pure validation helpers (no storage needed)
# ---------------------------------------------------------------------------


def _check_builtin(value: object, fd: FieldDef, path: str) -> list[str]:
    """Check *value* against a builtin type (string / number / bool)."""
    ft = fd.type
    if ft == "string":
        if not isinstance(value, str):
            return [f"'{path}' must be a string, got {type(value).__name__}"]
    elif ft == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return [f"'{path}' must be a number, got {type(value).__name__}"]
        return _check_number_bounds(value, fd.parameters, path)
    elif ft == "bool" and not isinstance(value, bool):
        return [f"'{path}' must be a boolean, got {type(value).__name__}"]
    return []


def _check_number_bounds(
    value: float,
    parameters: list[str],
    path: str,
) -> list[str]:
    """Check @min / @max constraints on a numeric *value*."""
    errors: list[str] = []
    for param in parameters:
        if param.startswith("@min="):
            min_val = float(param.split("=", 1)[1])
            if value < min_val:
                errors.append(f"'{path}': {value} is less than minimum {min_val}")
        elif param.startswith("@max="):
            max_val = float(param.split("=", 1)[1])
            if value > max_val:
                errors.append(f"'{path}': {value} exceeds maximum {max_val}")
    return errors


def _check_pattern(value: str, parameters: list[str], path: str) -> list[str]:
    """Check @pattern constraints on a string *value*."""
    errors: list[str] = []
    for param in parameters:
        if param.startswith("@pattern="):
            pattern = param.split("=", 1)[1]
            if not re.search(pattern, value):
                errors.append(f"'{path}': value does not match pattern '{pattern}'")
    return errors
