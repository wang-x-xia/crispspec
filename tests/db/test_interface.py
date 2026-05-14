"""Tests for db.interface module."""

from unittest.mock import Mock

from src.db.interface import Record, Storage

RESULT_COUNT = 2


def test_record_fields() -> None:
    """Test that Record fields are correctly set."""
    record = Record(id="REQ-1", type="requirement", data="name: Test", version="abc123")
    assert record.id == "REQ-1"
    assert record.type == "requirement"
    assert record.data == "name: Test"
    assert record.version == "abc123"


def test_storage_interface_get_by_id() -> None:
    """Test Storage.get_by_id returns correct record."""
    mock = Mock(spec=Storage)
    mock.get_by_id.return_value = Record(
        id="REQ-1",
        type="requirement",
        data="",
        version="v1",
    )
    result = mock.get_by_id("REQ-1")
    assert result is not None
    assert result.id == "REQ-1"


def test_storage_interface_list_by_type() -> None:
    """Test Storage.list_by_type returns all matching records."""
    mock = Mock(spec=Storage)
    mock.list_by_type.return_value = [
        Record(id="REQ-1", type="requirement", data="", version="v1"),
        Record(id="REQ-2", type="requirement", data="", version="v2"),
    ]
    results = mock.list_by_type("requirement")
    assert len(results) == RESULT_COUNT


def test_storage_interface_create() -> None:
    """Test Storage.create returns correct record."""
    mock = Mock(spec=Storage)
    mock.create.return_value = Record(
        id="REQ-1",
        type="requirement",
        data="",
        version="v1",
    )
    result = mock.create("requirement", "")
    assert result.id == "REQ-1"


def test_storage_interface_replace() -> None:
    """Test Storage.replace returns True on success."""
    mock = Mock(spec=Storage)
    mock.replace.return_value = True
    result = mock.replace("REQ-1", "new data", "v1")
    assert result is True


def test_storage_interface_delete() -> None:
    """Test Storage.delete returns True on success."""
    mock = Mock(spec=Storage)
    mock.delete.return_value = True
    result = mock.delete("REQ-1", "v1")
    assert result is True
