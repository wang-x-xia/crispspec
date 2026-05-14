"""Tests for db.sqlite module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.db import SqliteStorage

RESULT_COUNT = 3


@pytest.fixture
def temp_db() -> SqliteStorage:
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    storage = SqliteStorage(path)
    yield storage
    storage.close()
    Path(path).unlink()


def test_create_and_get(temp_db: SqliteStorage) -> None:
    """Test creating and retrieving a record."""
    record = temp_db.create("requirement", "name: Test Requirement")
    assert record.id == "REQ-1"
    assert record.type == "requirement"
    assert record.data == "name: Test Requirement"
    assert record.version is not None

    retrieved = temp_db.get_by_id("REQ-1")
    assert retrieved is not None
    assert retrieved.id == "REQ-1"
    assert retrieved.data == "name: Test Requirement"
    assert retrieved.version == record.version


def test_create_multiple_auto_increment(temp_db: SqliteStorage) -> None:
    """Test that auto-increment IDs are sequential."""
    r1 = temp_db.create("draft", "content: first")
    r2 = temp_db.create("draft", "content: second")
    r3 = temp_db.create("draft", "content: third")

    assert r1.id == "DRAFT-1"
    assert r2.id == "DRAFT-2"
    assert r3.id == "DRAFT-3"


def test_list_by_type(temp_db: SqliteStorage) -> None:
    """Test listing records by type."""
    temp_db.create("requirement", "data: 1")
    temp_db.create("requirement", "data: 2")
    temp_db.create("requirement", "data: 3")

    results = temp_db.list_by_type("requirement")
    assert len(results) == RESULT_COUNT
    assert all(r.type == "requirement" for r in results)


def test_list_empty_type(temp_db: SqliteStorage) -> None:
    """Test listing records for a type with no records."""
    results = temp_db.list_by_type("requirement")
    assert results == []


def test_replace(temp_db: SqliteStorage) -> None:
    """Test replacing an existing record."""
    record = temp_db.create("requirement", "original")
    assert record.data == "original"

    success = temp_db.replace("REQ-1", "updated", record.version)
    assert success is True

    updated = temp_db.get_by_id("REQ-1")
    assert updated.data == "updated"
    assert updated.version != record.version


def test_replace_nonexistent(temp_db: SqliteStorage) -> None:
    """Test replacing a nonexistent record returns False."""
    success = temp_db.replace("REQ-999", "data", "version")
    assert success is False


def test_delete(temp_db: SqliteStorage) -> None:
    """Test deleting a record."""
    record = temp_db.create("requirement", "to delete")
    success = temp_db.delete("REQ-1", record.version)
    assert success is True

    deleted = temp_db.get_by_id("REQ-1")
    assert deleted is None


def test_delete_nonexistent(temp_db: SqliteStorage) -> None:
    """Test deleting a nonexistent record returns False."""
    success = temp_db.delete("REQ-999", "version")
    assert success is False


def test_different_types_separate_tables(temp_db: SqliteStorage) -> None:
    """Test that different types use separate tables."""
    req = temp_db.create("requirement", "req data")
    draft = temp_db.create("draft", "draft data")

    assert req.id == "REQ-1"
    assert draft.id == "DRAFT-1"

    assert temp_db.get_by_id("REQ-1").data == "req data"
    assert temp_db.get_by_id("DRAFT-1").data == "draft data"

    req_list = temp_db.list_by_type("requirement")
    draft_list = temp_db.list_by_type("draft")
    assert len(req_list) == 1
    assert len(draft_list) == 1
    assert req_list[0].version is not None
    assert draft_list[0].version is not None


def test_get_nonexistent_id(temp_db: SqliteStorage) -> None:
    """Test getting a nonexistent ID returns None."""
    result = temp_db.get_by_id("REQ-999")
    assert result is None
