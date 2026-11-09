"""Consistency checks for artifacts.yaml.

The registry is a hand-maintained progress board.  These tests make sure it
cannot silently drift away from the code it describes: the type set in
``src/db/types.py``, the ID prefixes in ``src/db/mapping.py``, and the files
actually on disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.db.mapping import _TYPE_TO_PREFIX
from src.db.types import ALL_TYPES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "artifacts.yaml"

STAGE_ONE = 1
STAGE_TWO = 2
VALID_STATUS = frozenset({"done", "not-started"})
VALID_PRIORITY = frozenset({"P0", "P1", "P2"})
VALID_STAGES = frozenset({STAGE_ONE, STAGE_TWO})


@pytest.fixture(scope="module")
def registry() -> dict:
    """Load artifacts.yaml."""
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def artifacts(registry: dict) -> list[dict]:
    """Return the artifact entries of the registry."""
    return registry["artifacts"]


# ---------------------------------------------------------------------------
# Type set
# ---------------------------------------------------------------------------


def test_every_registered_type_is_covered(artifacts: list[dict]) -> None:
    """Every type in src/db/types.py has exactly one registry entry."""
    registered = [a["type"] for a in artifacts]
    assert sorted(registered) == sorted(ALL_TYPES)
    assert len(registered) == len(set(registered)), "duplicate registry entries"


def test_no_phantom_types(artifacts: list[dict]) -> None:
    """The registry does not mention types the code does not know."""
    known = set(ALL_TYPES)
    for artifact in artifacts:
        assert artifact["type"] in known, artifact["type"]
        for dep in artifact["depends_on"]:
            assert dep in known, f"{artifact['type']} -> {dep}"


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------


def test_id_prefixes_match_the_mapping(artifacts: list[dict]) -> None:
    """Each registry entry agrees with src/db/mapping.py."""
    for artifact in artifacts:
        assert artifact["id_prefix"] == _TYPE_TO_PREFIX[artifact["type"]], artifact["type"]


def test_status_matches_implementation(artifacts: list[dict]) -> None:
    """An artifact is 'done' exactly when it has a manager and tests."""
    for artifact in artifacts:
        implemented = artifact["manager"] is not None
        assert artifact["status"] == ("done" if implemented else "not-started"), artifact["type"]
        assert (artifact["tests"] is not None) == implemented, artifact["type"]


def test_field_values_are_valid(artifacts: list[dict]) -> None:
    """Status, priority and stage use the documented vocabulary."""
    for artifact in artifacts:
        assert artifact["status"] in VALID_STATUS, artifact["type"]
        assert artifact["priority"] in VALID_PRIORITY, artifact["type"]
        assert artifact["stage"] in VALID_STAGES, artifact["type"]


def test_domains_are_declared(registry: dict, artifacts: list[dict]) -> None:
    """Every artifact belongs to a domain declared in meta."""
    declared = set(registry["domains"])
    for artifact in artifacts:
        assert artifact["domain"] in declared, artifact["domain"]


# ---------------------------------------------------------------------------
# Files on disk
# ---------------------------------------------------------------------------


def test_definition_files_exist(artifacts: list[dict]) -> None:
    """Every referenced definition file is present."""
    for artifact in artifacts:
        path = PROJECT_ROOT / artifact["definition"]
        assert path.is_file(), artifact["definition"]


def test_implementation_files_exist(artifacts: list[dict]) -> None:
    """Every referenced manager and test file is present."""
    for artifact in artifacts:
        for key in ("manager", "tests"):
            value = artifact[key]
            if value is None:
                continue
            path = PROJECT_ROOT / value
            assert path.is_file(), value


# ---------------------------------------------------------------------------
# meta.counts
# ---------------------------------------------------------------------------


def test_meta_counts_are_accurate(registry: dict, artifacts: list[dict]) -> None:
    """The summary counts match the entries they summarise."""
    counts = registry["meta"]["counts"]
    assert counts["total"] == len(artifacts)
    assert counts["done"] == sum(1 for a in artifacts if a["status"] == "done")
    assert counts["not_started"] == sum(1 for a in artifacts if a["status"] == "not-started")
    assert counts["stage_1"] == sum(1 for a in artifacts if a["stage"] == STAGE_ONE)
    assert counts["stage_2"] == sum(1 for a in artifacts if a["stage"] == STAGE_TWO)
