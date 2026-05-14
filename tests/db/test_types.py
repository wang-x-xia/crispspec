"""Tests for db.types module."""

from src.db.types import ALL_TYPES


def test_all_types_non_empty() -> None:
    """Test that ALL_TYPES contains at least one type."""
    assert len(ALL_TYPES) > 0


def test_all_types_unique() -> None:
    """Test that all types in ALL_TYPES are unique."""
    assert len(ALL_TYPES) == len(set(ALL_TYPES))


def test_no_hyphen_types() -> None:
    """Test that no type contains underscores."""
    for t in ALL_TYPES:
        assert "_" not in t, f"Type {t} contains underscore"


def test_common_types_present() -> None:
    """Test that common types are present in ALL_TYPES."""
    expected = {"draft", "requirement", "user-story", "entity", "interface"}
    assert expected.issubset(set(ALL_TYPES))
