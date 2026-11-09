"""Module artifact management.

Provides the :class:`ModuleManager` class to create, retrieve, and validate
module definitions based on the YAML structure described in ``module.md``.

Module definitions are persisted via the ``Storage`` interface from ``src.db``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import yaml

from src.db.types import module as module_type

if TYPE_CHECKING:
    from src.db.interface import Storage

_ID_PATTERN = re.compile(r"^MOD-\d+$")
_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_NAME_MAX_LEN = 80
_DESC_MAX_LEN = 200

_ARTIFACT_ID_PATTERN = re.compile(
    r"^(API|ENT|EVT|ERR|PROC|ORCH|SUB|SCH)-\d+$",
)
_REF_PATTERNS: dict[str, re.Pattern[str]] = {
    "interface_ids": re.compile(r"^API-\d+$"),
    "process_ids": re.compile(r"^PROC-\d+$"),
    "constraint_ids": re.compile(r"^CON-\d+$"),
}


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ModuleType(Enum):
    """Type of a module (Stage 1 — CLI tool development)."""

    CLI = "CLI"
    INTERNAL_LIB = "INTERNAL_LIB"
    EXTERNAL_LIB = "EXTERNAL_LIB"


class Protocol(Enum):
    """Inter-module communication protocol."""

    PYTHON_API = "PYTHON_API"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Dependency:
    """A dependency on another module."""

    module_id: str
    protocol: Protocol
    required: bool


@dataclass
class CodeRef:
    """Maps an artifact to its source code location."""

    artifact_id: str
    path: str
    symbol: str


@dataclass
class ModuleDef:
    """A parsed module definition."""

    id: str
    name: str
    description: str
    type: ModuleType
    version: str
    owner: str
    used: bool = True
    deprecated: bool = False
    dependencies: list[Dependency] = field(default_factory=list)
    interface_ids: list[str] = field(default_factory=list)
    process_ids: list[str] = field(default_factory=list)
    constraint_ids: list[str] = field(default_factory=list)
    code_refs: list[CodeRef] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_enum(value: str, enum_cls: type[Enum], field_name: str) -> Enum:
    """Parse a string into an enum member, raising on failure."""
    for member in enum_cls:
        if member.value == value:
            return member
    valid = ", ".join(m.value for m in enum_cls)
    msg = f"Invalid {field_name}: '{value}' (valid: {valid})"
    raise ValueError(msg)


def parse_dependency(raw: dict) -> Dependency:
    """Parse a raw dict into a :class:`Dependency`.

    Raises:
        ValueError: If required keys are missing or values are invalid.

    """
    _require_keys(raw, ["module_id", "protocol", "required"], "Dependency")
    protocol = _parse_enum(raw["protocol"], Protocol, "protocol")
    if not isinstance(raw["required"], bool):
        msg = f"Dependency.required must be a boolean, got {type(raw['required']).__name__}"
        raise TypeError(msg)
    return Dependency(
        module_id=raw["module_id"],
        protocol=protocol,
        required=raw["required"],
    )


def parse_code_ref(raw: dict) -> CodeRef:
    """Parse a raw dict into a :class:`CodeRef`.

    Raises:
        ValueError: If required keys are missing or values are invalid.

    """
    _require_keys(raw, ["artifact_id", "path", "symbol"], "CodeRef")
    return CodeRef(
        artifact_id=raw["artifact_id"],
        path=raw["path"],
        symbol=raw["symbol"],
    )


def parse_module(raw: dict) -> ModuleDef:
    """Parse a raw YAML dict into a :class:`ModuleDef`.

    Raises:
        ValueError: If required keys are missing or values are invalid.

    """
    _require_keys(
        raw,
        ["id", "name", "description", "type", "version", "owner"],
        "Module",
    )

    mod_type = _parse_enum(raw["type"], ModuleType, "type")

    dependencies = [parse_dependency(d) for d in raw.get("dependencies", [])]
    code_refs = [parse_code_ref(c) for c in raw.get("code_refs", [])]

    return ModuleDef(
        id=raw["id"],
        name=raw["name"],
        description=raw["description"],
        type=mod_type,
        version=raw["version"],
        owner=raw["owner"],
        used=raw.get("used", True),
        deprecated=raw.get("deprecated", False),
        dependencies=dependencies,
        interface_ids=raw.get("interface_ids", []),
        process_ids=raw.get("process_ids", []),
        constraint_ids=raw.get("constraint_ids", []),
        code_refs=code_refs,
    )


def _require_keys(raw: dict, keys: list[str], context: str) -> None:
    """Raise :class:`ValueError` if any *keys* are missing from *raw*."""
    missing = [k for k in keys if k not in raw]
    if missing:
        msg = f"{context}: missing required keys: {', '.join(missing)}"
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_scalars(mod: ModuleDef) -> list[str]:
    """Validate scalar fields (id, name, description, version)."""
    errors: list[str] = []
    if not _ID_PATTERN.match(mod.id):
        errors.append(f"id: must match 'MOD-\\d+', got '{mod.id}'")
    if len(mod.name) > _NAME_MAX_LEN:
        errors.append(f"name: exceeds {_NAME_MAX_LEN} characters")
    if mod.name and not mod.name[0].isupper():
        errors.append(f"name: must start with an uppercase letter, got '{mod.name}'")
    if len(mod.description) > _DESC_MAX_LEN:
        errors.append(f"description: exceeds {_DESC_MAX_LEN} characters")
    if not _SEMVER_PATTERN.match(mod.version):
        errors.append(f"version: must be semver (e.g. '2.1.0'), got '{mod.version}'")
    return errors


def _validate_refs(mod: ModuleDef) -> list[str]:
    """Validate dependencies and reference ID lists."""
    errors: list[str] = []
    for i, dep in enumerate(mod.dependencies):
        if not _ID_PATTERN.match(dep.module_id):
            errors.append(
                f"dependencies[{i}].module_id: must match 'MOD-\\d+', got '{dep.module_id}'",
            )
    for field_name, pattern in _REF_PATTERNS.items():
        for i, ref_id in enumerate(getattr(mod, field_name)):
            if not pattern.match(ref_id):
                errors.append(
                    f"{field_name}[{i}]: must match '{pattern.pattern}', got '{ref_id}'",
                )
    return errors


def _validate_code_refs(code_refs: list[CodeRef]) -> list[str]:
    """Validate code reference entries."""
    errors: list[str] = []
    for i, cr in enumerate(code_refs):
        if not _ARTIFACT_ID_PATTERN.match(cr.artifact_id):
            errors.append(
                f"code_refs[{i}].artifact_id: must match a valid artifact ID pattern, "
                f"got '{cr.artifact_id}'",
            )
        if not cr.path:
            errors.append(f"code_refs[{i}].path: must not be empty")
        if not cr.symbol:
            errors.append(f"code_refs[{i}].symbol: must not be empty")
    return errors


def validate_module(mod: ModuleDef) -> list[str]:
    """Validate a :class:`ModuleDef` and return a list of error strings.

    An empty list means the definition is valid.
    """
    errors: list[str] = []
    errors.extend(_validate_scalars(mod))
    errors.extend(_validate_refs(mod))
    errors.extend(_validate_code_refs(mod.code_refs))
    return errors


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def _module_to_dict(mod: ModuleDef) -> dict:
    """Serialize a :class:`ModuleDef` into a YAML-friendly dict."""
    d: dict = {
        "id": mod.id,
        "name": mod.name,
        "description": mod.description,
        "type": mod.type.value,
        "version": mod.version,
        "owner": mod.owner,
        "used": mod.used,
        "deprecated": mod.deprecated,
    }
    if mod.dependencies:
        d["dependencies"] = [
            {
                "module_id": dep.module_id,
                "protocol": dep.protocol.value,
                "required": dep.required,
            }
            for dep in mod.dependencies
        ]
    if mod.interface_ids:
        d["interface_ids"] = mod.interface_ids
    if mod.process_ids:
        d["process_ids"] = mod.process_ids
    if mod.constraint_ids:
        d["constraint_ids"] = mod.constraint_ids
    if mod.code_refs:
        d["code_refs"] = [
            {
                "artifact_id": cr.artifact_id,
                "path": cr.path,
                "symbol": cr.symbol,
            }
            for cr in mod.code_refs
        ]
    return d


# ---------------------------------------------------------------------------
# ModuleManager class
# ---------------------------------------------------------------------------


class ModuleManager:
    """Manages module definitions backed by a :class:`Storage` instance."""

    def __init__(self, storage: Storage) -> None:
        """Initialize with the given *storage* backend."""
        self._storage = storage

    # -- public API ---------------------------------------------------------

    def create_module(self, raw: dict) -> str:
        """Parse, validate, and persist a module YAML.

        The storage layer owns ID assignment: the record ID it hands back is
        the canonical identity of the artifact.  If the YAML declares a
        different (merely well-formed) ID, the persisted artifact is
        rewritten to carry the canonical one, so an artifact can never hold
        two conflicting identities.

        Args:
            raw: A dict representing the module definition (as loaded from
                YAML).

        Returns:
            The record ID (``MOD-...``) assigned by the storage layer.

        Raises:
            ValueError: If parsing fails or the definition is invalid.

        """
        mod = parse_module(raw)
        errors = validate_module(mod)
        if errors:
            msg = "Module validation errors:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            raise ValueError(msg)

        payload = _module_to_dict(mod)
        record = self._storage.create(
            module_type,
            yaml.dump(payload, allow_unicode=True, default_flow_style=False),
        )
        if payload["id"] != record.id:
            payload["id"] = record.id
            self._storage.replace(
                record.id,
                yaml.dump(payload, allow_unicode=True, default_flow_style=False),
                record.version,
            )
        return record.id

    def get_module(self, module_id: str) -> dict | None:
        """Look up a module by its record *module_id*.

        Returns:
            The stored dict, or ``None`` if not found.

        """
        try:
            record = self._storage.get_by_id(module_id)
        except (ValueError, KeyError):
            return None
        if record is None:
            return None
        return yaml.safe_load(record.data)

    def list_modules(self) -> list[dict]:
        """Return all stored module definitions."""
        records = self._storage.list_by_type(module_type)
        return [yaml.safe_load(r.data) for r in records]

    def verify_module(self, module_id: str, data: dict) -> list[str]:
        """Verify *data* against the module stored under *module_id*.

        This re-parses and validates the provided *data* dict as a module
        definition.

        Returns:
            A list of error strings; empty means valid.

        """
        stored = self.get_module(module_id)
        if stored is None:
            return [f"Module '{module_id}' not found"]

        errors: list[str] = []
        try:
            mod = parse_module(data)
        except ValueError as exc:
            return [str(exc)]
        errors.extend(validate_module(mod))
        return errors
