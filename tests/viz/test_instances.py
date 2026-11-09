"""Tests for reading artifact instances out of a database."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.db.sqlite import SqliteStorage
from src.module.module import ModuleManager
from src.requirement.business_concept import BusinessConcept
from src.requirement.business_concept_storage import BusinessConceptStorage
from src.viz.catalog import Catalog, load_catalog
from src.viz.instances import load_instances

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a database holding one module and one business concept."""
    path = tmp_path / "crispspec.db"
    storage = SqliteStorage(str(path))

    manager = ModuleManager(storage)
    manager.create_module(
        {
            "id": "MOD-1",
            "name": "CrispSpec",
            "description": "命令行主模块",
            "type": "CLI",
            "version": "0.1.0",
            "owner": "core-team",
            "interface_ids": ["API-1"],
        },
    )

    concepts = BusinessConceptStorage(storage)
    concept = concepts.create(BusinessConcept(name="用户", description="系统用户"))
    concepts.add_mapping(concept.id, "as_object", "ENTITY", "ENT-3")

    storage.close()
    return path


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    """Return the artifact catalog."""
    return load_catalog()


def test_instances_are_read(db_path: Path, catalog: Catalog) -> None:
    """Every stored artifact becomes a node."""
    nodes, _edges = load_instances(db_path, catalog)
    ids = {node["id"] for node in nodes}
    assert {"MOD-1", "BC-1"} <= ids


def test_references_become_edges(db_path: Path, catalog: Catalog) -> None:
    """A typed reference becomes an edge."""
    _nodes, edges = load_instances(db_path, catalog)
    pairs = {(edge["source"], edge["target"], edge["relation"]) for edge in edges}
    assert ("MOD-1", "API-1", "EXPOSES") in pairs
    assert ("BC-1", "ENT-3", "AS_OBJECT") in pairs


def test_dangling_references_become_ghost_nodes(db_path: Path, catalog: Catalog) -> None:
    """A reference to an artifact that is not stored stays visible."""
    nodes, _edges = load_instances(db_path, catalog)
    ghosts = {node["id"]: node for node in nodes if node.get("missing")}
    assert "API-1" in ghosts
    assert ghosts["API-1"]["domain"] == "contract"


def test_missing_database_is_not_an_error(tmp_path: Path, catalog: Catalog) -> None:
    """A database that does not exist yields an empty graph."""
    nodes, edges = load_instances(tmp_path / "nope.db", catalog)
    assert nodes == []
    assert edges == []


def test_the_database_is_not_modified(db_path: Path, catalog: Catalog) -> None:
    """The visualiser opens the database read-only."""
    before = db_path.stat().st_mtime_ns
    load_instances(db_path, catalog)
    assert db_path.stat().st_mtime_ns == before
