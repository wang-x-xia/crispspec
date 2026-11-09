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
from src.viz.catalog import load_catalog
from src.viz.graph import build_payload

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


# ---------------------------------------------------------------------------
# Development mainline
# ---------------------------------------------------------------------------


def test_mainline_covers_every_artifact_exactly_once(registry: dict, artifacts: list[dict]) -> None:
    """Every artifact type belongs to exactly one phase of the mainline."""
    phases = registry["mainline"]
    covered = [name for phase in phases for name in phase["artifacts"]]
    assert len(covered) == len(set(covered)), "an artifact appears in two phases"
    assert sorted(covered) == sorted(a["type"] for a in artifacts)


def test_mainline_phase_ids_are_unique(registry: dict) -> None:
    """Two phases do not share an id."""
    ids = [phase["id"] for phase in registry["mainline"]]
    assert len(ids) == len(set(ids))


def test_mainline_phases_are_known_artifacts(registry: dict, artifacts: list[dict]) -> None:
    """A phase only names artifact types that exist."""
    known = {a["type"] for a in artifacts}
    for phase in registry["mainline"]:
        for name in phase["artifacts"]:
            assert name in known, f"{phase['id']}: {name}"


def test_mainline_handoffs_are_real_relations(registry: dict) -> None:
    """Every hand-off names a relation edge that the definitions declare.

    The mainline is a curated path through the artifact graph; if it
    cites an edge that does not exist, the mainline is a fiction.
    """
    edges = build_payload(load_catalog())["edges"]
    known = {(edge["source"], edge["target"], edge["relation"]) for edge in edges}
    for phase in registry["mainline"]:
        for handoff in phase.get("handoff", []):
            key = (handoff["from"], handoff["to"], handoff["relation"])
            assert key in known, f"{phase['id']}: {key}"


def test_mainline_handoffs_stay_inside_the_mainline(registry: dict) -> None:
    """A hand-off only moves between artifacts that are on the mainline."""
    on_mainline = {
        name for phase in registry["mainline"] for name in phase["artifacts"]
    }
    for phase in registry["mainline"]:
        for handoff in phase.get("handoff", []):
            assert handoff["from"] in on_mainline
            assert handoff["to"] in on_mainline
