"""Tests for requirement.business_concept_storage module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.db import SqliteStorage
from src.requirement.business_concept import BusinessConcept
from src.requirement.business_concept_storage import BusinessConceptStorage
from src.requirement.common import (
    ArtifactType,
    InvalidArtifactTypeError,
    InvalidBusinessConceptError,
    MappingAlreadyExistsError,
    NotFoundError,
)

CONCEPT_COUNT = 2

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def storage() -> BusinessConceptStorage:
    """Create a business concept storage backed by a temporary SQLite file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = SqliteStorage(path)
    s = BusinessConceptStorage(db)
    yield s
    db.close()
    Path(path).unlink()


def concept(name: str = "VIP会员") -> BusinessConcept:
    """Return an unsaved business concept."""
    return BusinessConcept(
        name=name,
        description="享受优先退款权益的高价值用户",
        defined=True,
    )


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


def test_get_by_id_found(storage: BusinessConceptStorage) -> None:
    """A stored concept can be fetched by ID."""
    created = storage.create(concept())
    found = storage.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id
    assert found.name == "VIP会员"
    assert found.description == "享受优先退款权益的高价值用户"
    assert found.defined is True


def test_get_by_id_not_found(storage: BusinessConceptStorage) -> None:
    """An unknown ID yields None."""
    assert storage.get_by_id("BC-999") is None


# ---------------------------------------------------------------------------
# get_by_name
# ---------------------------------------------------------------------------


def test_get_by_name_found(storage: BusinessConceptStorage) -> None:
    """A stored concept can be fetched by name."""
    created = storage.create(concept())
    found = storage.get_by_name("VIP会员")
    assert found is not None
    assert found.id == created.id


def test_get_by_name_not_found(storage: BusinessConceptStorage) -> None:
    """An unknown name yields None."""
    storage.create(concept())
    assert storage.get_by_name("普通会员") is None


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


def test_list_all(storage: BusinessConceptStorage) -> None:
    """Every stored concept is listed."""
    storage.create(concept("VIP会员"))
    storage.create(concept("退款单"))

    all_concepts = storage.list_all()
    assert len(all_concepts) == CONCEPT_COUNT
    assert {c.name for c in all_concepts} == {"VIP会员", "退款单"}


def test_list_all_empty(storage: BusinessConceptStorage) -> None:
    """Listing with nothing stored yields an empty list."""
    assert storage.list_all() == []


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create_assigns_incrementing_id(storage: BusinessConceptStorage) -> None:
    """IDs are assigned by the storage layer and increment."""
    first = storage.create(concept("VIP会员"))
    second = storage.create(concept("退款单"))
    assert first.id == "BC-1"
    assert second.id == "BC-2"


def test_create_starts_with_empty_mappings(storage: BusinessConceptStorage) -> None:
    """A newly created concept has no mappings."""
    created = storage.create(concept())
    assert created.mappings == []
    assert storage.get_by_id(created.id).mappings == []


def test_create_persists_canonical_id(storage: BusinessConceptStorage) -> None:
    """The persisted concept carries the ID assigned by the storage."""
    created = storage.create(concept())
    assert storage.get_by_id(created.id).id == created.id


def test_create_rejects_empty_name(storage: BusinessConceptStorage) -> None:
    """A concept without a name is rejected."""
    with pytest.raises(InvalidBusinessConceptError, match="name: must not be empty"):
        storage.create(BusinessConcept(name="", description="d"))


def test_create_rejects_long_name(storage: BusinessConceptStorage) -> None:
    """An over-long name is rejected."""
    with pytest.raises(InvalidBusinessConceptError, match="name: exceeds 80"):
        storage.create(concept("名" * 81))


def test_create_rejects_long_description(storage: BusinessConceptStorage) -> None:
    """An over-long description is rejected."""
    bc = concept()
    bc.description = "d" * 201
    with pytest.raises(InvalidBusinessConceptError, match="description: exceeds 200"):
        storage.create(bc)


# ---------------------------------------------------------------------------
# add_mapping
# ---------------------------------------------------------------------------


def test_add_mapping(storage: BusinessConceptStorage) -> None:
    """A mapping is added and persisted."""
    created = storage.create(concept())
    updated = storage.add_mapping(created.id, "ROLE", "ROLE-3")

    assert len(updated.mappings) == 1
    mapping = updated.mappings[0]
    assert mapping.artifact_type == ArtifactType.ROLE
    assert mapping.artifact_id == "ROLE-3"

    stored = storage.get_by_id(created.id)
    assert stored.mappings[0].artifact_id == "ROLE-3"


def test_add_mapping_accepts_every_allowed_type(storage: BusinessConceptStorage) -> None:
    """Any allowed artifact type may be mapped."""
    created = storage.create(concept())
    cases = [
        ("MODULE", "MOD-1"),
        ("ENTITY", "ENT-1"),
        ("INTERFACE", "API-1"),
        ("ORCHESTRATION", "ORCH-1"),
        ("REACTION", "SUB-1"),
        ("SCHEDULE", "SCH-1"),
        ("EVENT", "EVT-1"),
        ("ERROR", "ERR-1"),
        ("ENTITY_FIELD", "ENT-1.expected_completion"),
        ("STATE_CHANGE", "PROC-1"),
        ("INTERFACE_RESPONSE", "API-1"),
        ("SIDE_EFFECT", "PROC-1"),
    ]
    for artifact_type, artifact_id in cases:
        storage.add_mapping(created.id, artifact_type, artifact_id)

    stored = storage.get_by_id(created.id)
    assert len(stored.mappings) == len(cases)


def test_add_mapping_supports_several_targets(storage: BusinessConceptStorage) -> None:
    """One concept may be realised by several artifacts at once."""
    created = storage.create(concept())
    storage.add_mapping(created.id, "ENTITY", "ENT-3")
    storage.add_mapping(created.id, "INTERFACE", "API-20")
    storage.add_mapping(created.id, "ROLE", "ROLE-1")

    stored = storage.get_by_id(created.id)
    assert [(m.artifact_type, m.artifact_id) for m in stored.mappings] == [
        (ArtifactType.ENTITY, "ENT-3"),
        (ArtifactType.INTERFACE, "API-20"),
        (ArtifactType.ROLE, "ROLE-1"),
    ]


def test_add_mapping_supports_several_targets_of_one_type(
    storage: BusinessConceptStorage,
) -> None:
    """The same kind of artifact may be mapped more than once."""
    created = storage.create(concept())
    storage.add_mapping(created.id, "INTERFACE", "API-1")
    storage.add_mapping(created.id, "INTERFACE", "API-2")

    stored = storage.get_by_id(created.id)
    assert [m.artifact_id for m in stored.mappings] == ["API-1", "API-2"]


def test_add_mapping_already_exists(storage: BusinessConceptStorage) -> None:
    """Mapping the very same artifact twice is rejected."""
    created = storage.create(concept())
    storage.add_mapping(created.id, "ROLE", "ROLE-3")
    with pytest.raises(MappingAlreadyExistsError, match="already mapped"):
        storage.add_mapping(created.id, "ROLE", "ROLE-3")


def test_add_mapping_invalid_artifact_type(storage: BusinessConceptStorage) -> None:
    """An unknown artifact type is rejected."""
    created = storage.create(concept())
    with pytest.raises(InvalidArtifactTypeError, match="Invalid artifact type"):
        storage.add_mapping(created.id, "NONSENSE", "ROLE-3")


def test_add_mapping_unknown_concept(storage: BusinessConceptStorage) -> None:
    """Mapping on an unknown concept raises."""
    with pytest.raises(NotFoundError, match="Business concept not found"):
        storage.add_mapping("BC-999", "ROLE", "ROLE-3")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_changes_non_mapping_fields(storage: BusinessConceptStorage) -> None:
    """Name, description and defined can be changed."""
    created = storage.create(concept())
    updated = storage.update(
        created.id,
        name="VIP客户",
        description="更新后的描述",
        defined=False,
    )

    assert updated is not None
    assert updated.name == "VIP客户"
    assert updated.description == "更新后的描述"
    assert updated.defined is False

    stored = storage.get_by_id(created.id)
    assert stored.name == "VIP客户"
    assert stored.defined is False


def test_update_keeps_mappings(storage: BusinessConceptStorage) -> None:
    """Updating a concept does not disturb its mappings."""
    created = storage.create(concept())
    storage.add_mapping(created.id, "ROLE", "ROLE-3")
    updated = storage.update(created.id, name="VIP客户")
    assert updated is not None
    assert updated.mappings[0].artifact_id == "ROLE-3"


def test_update_unknown_concept(storage: BusinessConceptStorage) -> None:
    """Updating an unknown concept yields None."""
    assert storage.update("BC-999", name="x") is None


def test_update_rejects_mapping_fields(storage: BusinessConceptStorage) -> None:
    """Mapping fields cannot be updated directly."""
    created = storage.create(concept())
    with pytest.raises(InvalidBusinessConceptError, match="Cannot update field"):
        storage.update(created.id, mappings=[])


def test_update_rejects_invalid_result(storage: BusinessConceptStorage) -> None:
    """An update that violates validation is rejected."""
    created = storage.create(concept())
    with pytest.raises(InvalidBusinessConceptError, match="name: must not be empty"):
        storage.update(created.id, name="")
