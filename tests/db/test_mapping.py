"""Tests for db.mapping module."""

from src.db.mapping import (
    generate_id,
    get_all_types,
    is_valid_type,
    parse_id,
    prefix_to_type,
    type_to_prefix,
)

MAGIC_VALUE_42 = 42
MAGIC_VALUE_100 = 100
TYPE_COUNT_THRESHOLD = 30


def test_type_to_prefix_valid() -> None:
    """Test type_to_prefix with valid types."""
    assert type_to_prefix("draft") == "DRAFT"
    assert type_to_prefix("requirement") == "REQ"
    assert type_to_prefix("user-story") == "US"


def test_type_to_prefix_invalid() -> None:
    """Test type_to_prefix raises ValueError for invalid type."""
    with __import__("pytest").raises(ValueError, match="Unknown type"):
        type_to_prefix("invalid")


def test_prefix_to_type_valid() -> None:
    """Test prefix_to_type with valid prefixes."""
    assert prefix_to_type("DRAFT") == "draft"
    assert prefix_to_type("REQ") == "requirement"
    assert prefix_to_type("US") == "user-story"


def test_prefix_to_type_invalid() -> None:
    """Test prefix_to_type raises ValueError for invalid prefix."""
    with __import__("pytest").raises(ValueError, match="Unknown prefix"):
        prefix_to_type("INVALID")


def test_generate_id() -> None:
    """Test generate_id produces correct ID format."""
    id_ = generate_id("requirement", 1)
    assert id_ == "REQ-1"
    assert id_ == generate_id("requirement", 1)


def test_parse_id() -> None:
    """Test parse_id correctly splits ID into type and number."""
    type_, num = parse_id("REQ-42")
    assert type_ == "requirement"
    assert num == MAGIC_VALUE_42


def test_parse_id_roundtrip() -> None:
    """Test parse_id and generate_id are inverses."""
    original_type = "entity"
    id_ = generate_id(original_type, MAGIC_VALUE_100)
    parsed_type, parsed_num = parse_id(id_)
    assert parsed_type == original_type
    assert parsed_num == MAGIC_VALUE_100


def test_is_valid_type() -> None:
    """Test is_valid_type returns correct boolean."""
    assert is_valid_type("draft") is True
    assert is_valid_type("requirement") is True
    assert is_valid_type("invalid") is False


def test_get_all_types() -> None:
    """Test get_all_types returns all defined types."""
    types = get_all_types()
    assert "draft" in types
    assert "requirement" in types
    assert len(types) > TYPE_COUNT_THRESHOLD
