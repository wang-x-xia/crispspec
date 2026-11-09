"""Tests for module.module module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.db import SqliteStorage
from src.module.module import (
    ModuleManager,
    ModuleType,
    Protocol,
    parse_code_ref,
    parse_dependency,
    parse_module,
    validate_module,
)

MODULE_COUNT = 2

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager() -> ModuleManager:
    """Create a ModuleManager backed by a temporary SQLite storage."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = SqliteStorage(path)
    m = ModuleManager(db)
    yield m
    db.close()
    Path(path).unlink()


def valid_module(**overrides: object) -> dict:
    """Return a minimal valid module definition, with optional overrides."""
    raw: dict = {
        "id": "MOD-1",
        "name": "CrispSpec",
        "description": "CrispSpec 命令行工具主模块",
        "type": "CLI",
        "version": "0.1.0",
        "owner": "core-team",
    }
    raw.update(overrides)
    return raw


# ---------------------------------------------------------------------------
# parse_dependency
# ---------------------------------------------------------------------------


def test_parse_dependency() -> None:
    """A well-formed dependency is parsed into a Dependency."""
    dep = parse_dependency(
        {"module_id": "MOD-2", "protocol": "PYTHON_API", "required": True},
    )
    assert dep.module_id == "MOD-2"
    assert dep.protocol == Protocol.PYTHON_API
    assert dep.required is True


def test_parse_dependency_missing_key() -> None:
    """A missing required key raises ValueError."""
    with pytest.raises(ValueError, match="missing required keys"):
        parse_dependency({"module_id": "MOD-2", "protocol": "PYTHON_API"})


def test_parse_dependency_invalid_protocol() -> None:
    """An unknown protocol raises ValueError."""
    with pytest.raises(ValueError, match="Invalid protocol"):
        parse_dependency(
            {"module_id": "MOD-2", "protocol": "GRPC", "required": True},
        )


def test_parse_dependency_non_bool_required() -> None:
    """A non-boolean `required` raises TypeError."""
    with pytest.raises(TypeError, match="must be a boolean"):
        parse_dependency(
            {"module_id": "MOD-2", "protocol": "PYTHON_API", "required": "yes"},
        )


# ---------------------------------------------------------------------------
# parse_code_ref
# ---------------------------------------------------------------------------


def test_parse_code_ref() -> None:
    """A well-formed code ref is parsed into a CodeRef."""
    ref = parse_code_ref(
        {"artifact_id": "API-1", "path": "src/cli/create.py", "symbol": "Create"},
    )
    assert ref.artifact_id == "API-1"
    assert ref.path == "src/cli/create.py"
    assert ref.symbol == "Create"


def test_parse_code_ref_missing_key() -> None:
    """A missing required key raises ValueError."""
    with pytest.raises(ValueError, match="missing required keys"):
        parse_code_ref({"artifact_id": "API-1", "path": "src/cli/create.py"})


# ---------------------------------------------------------------------------
# parse_module
# ---------------------------------------------------------------------------


def test_parse_module_minimal() -> None:
    """Optional fields fall back to their documented defaults."""
    mod = parse_module(valid_module())
    assert mod.id == "MOD-1"
    assert mod.type == ModuleType.CLI
    assert mod.used is True
    assert mod.deprecated is False
    assert mod.dependencies == []
    assert mod.code_refs == []


def test_parse_module_full() -> None:
    """Every field of a fully populated module is parsed."""
    mod = parse_module(
        valid_module(
            dependencies=[
                {"module_id": "MOD-2", "protocol": "PYTHON_API", "required": True},
            ],
            interface_ids=["API-1"],
            process_ids=["PROC-1"],
            constraint_ids=["CON-1"],
            code_refs=[
                {"artifact_id": "API-1", "path": "a.py", "symbol": "A"},
            ],
        ),
    )
    assert len(mod.dependencies) == 1
    assert mod.interface_ids == ["API-1"]
    assert mod.process_ids == ["PROC-1"]
    assert mod.constraint_ids == ["CON-1"]
    assert len(mod.code_refs) == 1


def test_parse_module_missing_key() -> None:
    """A missing required key raises ValueError."""
    raw = valid_module()
    del raw["version"]
    with pytest.raises(ValueError, match="missing required keys"):
        parse_module(raw)


def test_parse_module_invalid_type() -> None:
    """An unknown module type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid type"):
        parse_module(valid_module(type="MICROSERVICE"))


# ---------------------------------------------------------------------------
# validate_module
# ---------------------------------------------------------------------------


def test_validate_module_accepts_valid() -> None:
    """A valid module produces no errors."""
    assert validate_module(parse_module(valid_module())) == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", "MODULE-1", "must match 'MOD-\\d+'"),
        ("id", "MOD-1x", "must match 'MOD-\\d+'"),
        ("name", "lowercase", "must start with an uppercase letter"),
        ("name", "A" * 81, "exceeds 80 characters"),
        ("description", "d" * 201, "exceeds 200 characters"),
        ("version", "1.0", "must be semver"),
        ("version", "v1.0.0", "must be semver"),
    ],
)
def test_validate_module_scalar_errors(
    field: str,
    value: str,
    message: str,
) -> None:
    """Scalar field constraints are enforced."""
    errors = validate_module(parse_module(valid_module(**{field: value})))
    assert any(message in e for e in errors), errors


def test_validate_module_bad_dependency_id() -> None:
    """A dependency must reference a valid module ID."""
    mod = parse_module(
        valid_module(
            dependencies=[
                {"module_id": "API-1", "protocol": "PYTHON_API", "required": True},
            ],
        ),
    )
    errors = validate_module(mod)
    assert any("dependencies[0].module_id" in e for e in errors), errors


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("interface_ids", ["PROC-1"]),
        ("process_ids", ["API-1"]),
        ("constraint_ids", ["MOD-1"]),
    ],
)
def test_validate_module_bad_ref_lists(field: str, value: list[str]) -> None:
    """Reference lists only accept IDs of their own artifact type."""
    errors = validate_module(parse_module(valid_module(**{field: value})))
    assert any(field in e for e in errors), errors


def test_validate_module_bad_code_ref_artifact_id() -> None:
    """A code ref must reference a contract or behaviour artifact."""
    mod = parse_module(
        valid_module(
            code_refs=[
                {"artifact_id": "MOD-1", "path": "a.py", "symbol": "A"},
            ],
        ),
    )
    errors = validate_module(mod)
    assert any("code_refs[0].artifact_id" in e for e in errors), errors


@pytest.mark.parametrize(
    "code_ref",
    [
        {"artifact_id": "API-1", "path": "", "symbol": "A"},
        {"artifact_id": "API-1", "path": "a.py", "symbol": ""},
    ],
)
def test_validate_module_empty_code_ref_fields(code_ref: dict) -> None:
    """A code ref must have a non-empty path and symbol."""
    mod = parse_module(valid_module(code_refs=[code_ref]))
    errors = validate_module(mod)
    assert len(errors) == 1, errors


# ---------------------------------------------------------------------------
# ModuleManager
# ---------------------------------------------------------------------------


def test_create_module(manager: ModuleManager) -> None:
    """A valid module is persisted and gets a MOD- prefixed ID."""
    record_id = manager.create_module(valid_module())
    assert record_id == "MOD-1"

    stored = manager.get_module(record_id)
    assert stored is not None
    assert stored["name"] == "CrispSpec"
    assert stored["type"] == "CLI"


def test_create_module_persists_canonical_id(manager: ModuleManager) -> None:
    """The persisted artifact carries the ID assigned by the storage."""
    record_id = manager.create_module(valid_module(id="MOD-001"))
    stored = manager.get_module(record_id)
    assert stored is not None
    assert stored["id"] == record_id


def test_create_module_invalid_raises(manager: ModuleManager) -> None:
    """An invalid module is rejected and nothing is persisted."""
    with pytest.raises(ValueError, match="Module validation errors"):
        manager.create_module(valid_module(version="not-semver"))
    assert manager.list_modules() == []


def test_create_module_parse_error_raises(manager: ModuleManager) -> None:
    """A structurally broken module is rejected."""
    with pytest.raises(ValueError, match="missing required keys"):
        manager.create_module({"id": "MOD-1"})


def test_get_module_not_found(manager: ModuleManager) -> None:
    """Looking up an unknown module returns None."""
    assert manager.get_module("MOD-999") is None


def test_list_modules(manager: ModuleManager) -> None:
    """All stored modules are listed."""
    manager.create_module(valid_module(name="First"))
    manager.create_module(valid_module(name="Second"))

    modules = manager.list_modules()
    assert len(modules) == MODULE_COUNT
    assert {m["name"] for m in modules} == {"First", "Second"}


def test_list_modules_empty(manager: ModuleManager) -> None:
    """Listing with nothing stored returns an empty list."""
    assert manager.list_modules() == []


def test_verify_module_valid(manager: ModuleManager) -> None:
    """A valid module verifies without errors."""
    record_id = manager.create_module(valid_module())
    stored = manager.get_module(record_id)
    assert stored is not None
    assert manager.verify_module(record_id, stored) == []


def test_verify_module_invalid(manager: ModuleManager) -> None:
    """Verification reports the errors of the supplied definition."""
    record_id = manager.create_module(valid_module())
    errors = manager.verify_module(record_id, valid_module(version="bad"))
    assert any("must be semver" in e for e in errors), errors


def test_verify_module_not_found(manager: ModuleManager) -> None:
    """Verifying against an unknown module reports it."""
    errors = manager.verify_module("MOD-999", valid_module())
    assert errors == ["Module 'MOD-999' not found"]
