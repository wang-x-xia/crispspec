"""Tests for schema.schema module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.db import SqliteStorage
from src.schema.schema import (
    Schema,
    TypeKind,
    classify_type,
    parse_field,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def schema() -> Schema:
    """Create a Schema backed by a temporary SQLite storage."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = SqliteStorage(path)
    s = Schema(db)
    yield s
    db.close()
    Path(path).unlink()


# ---------------------------------------------------------------------------
# parse_field
# ---------------------------------------------------------------------------


def test_parse_field_full_format() -> None:
    """Parse a complete 'type;params;desc' string."""
    fd = parse_field("string;@required;用户名称")
    assert fd.type == "string"
    assert fd.parameters == ["@required"]
    assert fd.description == "用户名称"


def test_parse_field_no_params() -> None:
    """Empty params section is allowed."""
    fd = parse_field("number;;用户年龄")
    assert fd.type == "number"
    assert fd.parameters == []
    assert fd.description == "用户年龄"


def test_parse_field_no_desc() -> None:
    """Empty description section is allowed."""
    fd = parse_field("@TYPE-abc;@required;")
    assert fd.type == "@TYPE-abc"
    assert fd.parameters == ["@required"]
    assert fd.description == ""


def test_parse_field_no_params_no_desc() -> None:
    """Both params and description can be empty."""
    fd = parse_field("bool;;")
    assert fd.type == "bool"
    assert fd.parameters == []
    assert fd.description == ""


def test_parse_field_multiple_params() -> None:
    """Comma-separated parameters are split correctly."""
    fd = parse_field("number;@min=1,@max=65535;服务端口")
    assert fd.parameters == ["@min=1", "@max=65535"]


def test_parse_field_missing_semicolons() -> None:
    """Raise ValueError when semicolons are missing."""
    with pytest.raises(ValueError, match="Invalid field definition"):
        parse_field("string")


def test_parse_field_one_semicolon() -> None:
    """Raise ValueError when only one semicolon is present."""
    with pytest.raises(ValueError, match="Invalid field definition"):
        parse_field("string;@required")


def test_parse_field_desc_with_semicolons() -> None:
    """Semicolons inside the description are preserved."""
    fd = parse_field("string;;a;b;c")
    assert fd.description == "a;b;c"


# ---------------------------------------------------------------------------
# classify_type / FieldDef.kind
# ---------------------------------------------------------------------------


def test_classify_type_primitives() -> None:
    """String, number, bool are PRIMITIVE."""
    for t in ("string", "number", "bool"):
        assert classify_type(t) == TypeKind.PRIMITIVE


def test_classify_type_composite() -> None:
    """Object and array are COMPOSITE."""
    assert classify_type("object") == TypeKind.COMPOSITE
    assert classify_type("array") == TypeKind.COMPOSITE


def test_classify_type_inline_link() -> None:
    """Local type references '@.Name' are INLINE_LINK."""
    assert classify_type("@.User") == TypeKind.INLINE_LINK
    assert classify_type("@.Address") == TypeKind.INLINE_LINK


def test_classify_type_external_link() -> None:
    """@TYPE-{ID} and @TYPE-{ID}.{name} are EXTERNAL_LINK."""
    assert classify_type("@TYPE-abc123") == TypeKind.EXTERNAL_LINK
    assert classify_type("@TYPE-abc123.DatabaseConfig") == TypeKind.EXTERNAL_LINK


def test_classify_type_unknown() -> None:
    """Unrecognised type strings return None."""
    assert classify_type("integer") is None
    assert classify_type("@email") is None
    assert classify_type("") is None


def test_kind_property() -> None:
    """FieldDef.kind derives from the type string."""
    assert parse_field("string;@required;名称").kind == TypeKind.PRIMITIVE
    assert parse_field("@.User;@required;用户").kind == TypeKind.INLINE_LINK
    assert parse_field("@TYPE-x.DB;@required;数据库").kind == TypeKind.EXTERNAL_LINK
    assert parse_field("@TYPE-x;;引用").kind == TypeKind.EXTERNAL_LINK
    assert parse_field("integer;;描述").kind is None


# ---------------------------------------------------------------------------
# create_type — structure validation
# ---------------------------------------------------------------------------


def test_create_type_missing_self(schema: Schema) -> None:
    """Reject a dict without __self."""
    with pytest.raises(ValueError, match="__self"):
        schema.create_type({})


def test_create_type_extra_keys(schema: Schema) -> None:
    """Reject top-level keys other than __self and __typedefs."""
    with pytest.raises(ValueError, match="Unexpected"):
        schema.create_type({
            "__self": "string;;描述",
            "extra": "string;;不允许",
        })


# ---------------------------------------------------------------------------
# create_type — object __self
# ---------------------------------------------------------------------------


def test_create_type_object(schema: Schema) -> None:
    """Create a type whose __self is an object."""
    tid = schema.create_type({
        "__self": {
            "name": "string;@required;用户名称",
            "age": "number;;用户年龄",
        },
    })
    assert tid.startswith("TYPE-")


def test_create_type_nested_object(schema: Schema) -> None:
    """Object __self with nested object children."""
    tid = schema.create_type({
        "__self": {
            "host": "string;@required;主机",
            "ssl": {
                "enabled": "bool;;启用",
                "cert": "string;;证书",
            },
        },
    })
    assert tid.startswith("TYPE-")


# ---------------------------------------------------------------------------
# create_type — string __self
# ---------------------------------------------------------------------------


def test_create_type_string(schema: Schema) -> None:
    """Create a type whose __self is a string definition."""
    tid = schema.create_type({
        "__self": "string;@pattern=^[^@]+@[^@]+$;邮箱",
    })
    assert tid.startswith("TYPE-")


# ---------------------------------------------------------------------------
# create_type — array __self
# ---------------------------------------------------------------------------


def test_create_type_array(schema: Schema) -> None:
    """Create a type whose __self is an array."""
    tid = schema.create_type({
        "__self": ["string;@required;标签"],
    })
    assert tid.startswith("TYPE-")


# ---------------------------------------------------------------------------
# create_type — with __typedefs
# ---------------------------------------------------------------------------


def test_create_type_with_typedefs(schema: Schema) -> None:
    """Create a type with __self and __typedefs."""
    tid = schema.create_type({
        "__self": {
            "server": "@.ServerConfig;@required;服务器",
        },
        "__typedefs": {
            "ServerConfig": {
                "host": "string;@required;主机",
                "port": "number;@min=1,@max=65535;端口",
            },
        },
    })
    assert tid.startswith("TYPE-")


def test_create_type_array_with_typedefs(schema: Schema) -> None:
    """Array __self referencing __typedefs entry."""
    tid = schema.create_type({
        "__self": ["@.Item;@required;列表"],
        "__typedefs": {
            "Item": {
                "name": "string;@required;名称",
            },
        },
    })
    assert tid.startswith("TYPE-")


# ---------------------------------------------------------------------------
# create_type — definition validation errors
# ---------------------------------------------------------------------------


def test_create_type_invalid_type_str(schema: Schema) -> None:
    """Reject unknown type strings in __self."""
    with pytest.raises(ValueError, match="Unknown type"):
        schema.create_type({"__self": {"x": "integer;;描述"}})


def test_create_type_invalid_param_prefix(schema: Schema) -> None:
    """Reject parameters that don't start with @."""
    with pytest.raises(ValueError, match="Parameter must start with"):
        schema.create_type({"__self": {"x": "string;required;描述"}})


def test_create_type_empty_local_ref(schema: Schema) -> None:
    """Reject an empty local type reference '@.'."""
    with pytest.raises(ValueError, match="Empty local type reference"):
        schema.create_type({"__self": {"x": "@.;;描述"}})


# ---------------------------------------------------------------------------
# get_type
# ---------------------------------------------------------------------------


def test_get_type_found(schema: Schema) -> None:
    """Return stored data when ID matches."""
    tid = schema.create_type({
        "__self": {"name": "string;@required;名称"},
    })
    result = schema.get_type(tid)
    assert result is not None
    assert "__self" in result


def test_get_type_not_found(schema: Schema) -> None:
    """Return None for a nonexistent ID."""
    assert schema.get_type("TYPE-nonexistent") is None


def test_get_type_with_typedefs(schema: Schema) -> None:
    """Returned dict includes __typedefs when present."""
    tid = schema.create_type({
        "__self": {"x": "@.Foo;@required;字段"},
        "__typedefs": {"Foo": {"y": "string;;子字段"}},
    })
    result = schema.get_type(tid)
    assert result is not None
    assert "__typedefs" in result
    assert "Foo" in result["__typedefs"]


# ---------------------------------------------------------------------------
# verify_type — valid data
# ---------------------------------------------------------------------------


def test_verify_object_valid(schema: Schema) -> None:
    """All fields present and correct types."""
    tid = schema.create_type({
        "__self": {
            "name": "string;@required;名称",
            "age": "number;;年龄",
            "enabled": "bool;;启用",
        },
    })
    errors = schema.verify_type(tid, {
        "name": "Alice",
        "age": 30,
        "enabled": True,
    })
    assert errors == []


def test_verify_string_valid(schema: Schema) -> None:
    """String __self validates correctly."""
    tid = schema.create_type({
        "__self": "string;@pattern=^[A-Z]+$;大写",
    })
    assert schema.verify_type(tid, "HELLO") == []


def test_verify_array_valid(schema: Schema) -> None:
    """Array __self validates correctly."""
    tid = schema.create_type({
        "__self": ["string;@required;标签"],
    })
    assert schema.verify_type(tid, ["a", "b", "c"]) == []


def test_verify_optional_missing(schema: Schema) -> None:
    """Optional fields can be omitted."""
    tid = schema.create_type({
        "__self": {
            "name": "string;@required;名称",
            "age": "number;;年龄",
        },
    })
    assert schema.verify_type(tid, {"name": "Bob"}) == []


def test_verify_number_in_bounds(schema: Schema) -> None:
    """Number within @min/@max passes."""
    tid = schema.create_type({
        "__self": {"port": "number;@min=1,@max=65535;端口"},
    })
    assert schema.verify_type(tid, {"port": 8080}) == []


# ---------------------------------------------------------------------------
# verify_type — errors
# ---------------------------------------------------------------------------


def test_verify_type_not_found(schema: Schema) -> None:
    """Return error for nonexistent type ID."""
    errors = schema.verify_type("TYPE-ghost", {})
    assert any("not found" in e for e in errors)


def test_verify_required_missing(schema: Schema) -> None:
    """Detect missing @required fields."""
    tid = schema.create_type({
        "__self": {"name": "string;@required;名称"},
    })
    errors = schema.verify_type(tid, {})
    assert any("required" in e for e in errors)


def test_verify_wrong_string(schema: Schema) -> None:
    """Detect non-string value for a string field."""
    tid = schema.create_type({"__self": {"x": "string;;字段"}})
    errors = schema.verify_type(tid, {"x": 123})
    assert any("string" in e for e in errors)


def test_verify_wrong_number(schema: Schema) -> None:
    """Detect non-number value for a number field."""
    tid = schema.create_type({"__self": {"x": "number;;字段"}})
    errors = schema.verify_type(tid, {"x": "abc"})
    assert any("number" in e for e in errors)


def test_verify_bool_rejects_int(schema: Schema) -> None:
    """Bool field should reject int values."""
    tid = schema.create_type({"__self": {"x": "bool;;字段"}})
    errors = schema.verify_type(tid, {"x": 1})
    assert any("boolean" in e for e in errors)


def test_verify_number_rejects_bool(schema: Schema) -> None:
    """Number field should reject bool values."""
    tid = schema.create_type({"__self": {"x": "number;;字段"}})
    errors = schema.verify_type(tid, {"x": True})
    assert any("number" in e for e in errors)


def test_verify_min_violation(schema: Schema) -> None:
    """Detect value below @min."""
    tid = schema.create_type({"__self": {"x": "number;@min=10;字段"}})
    errors = schema.verify_type(tid, {"x": 5})
    assert any("minimum" in e for e in errors)


def test_verify_max_violation(schema: Schema) -> None:
    """Detect value above @max."""
    tid = schema.create_type({"__self": {"x": "number;@max=100;字段"}})
    errors = schema.verify_type(tid, {"x": 200})
    assert any("maximum" in e for e in errors)


def test_verify_pattern_violation(schema: Schema) -> None:
    """Detect value not matching @pattern."""
    tid = schema.create_type({"__self": {"x": "string;@pattern=^[A-Z]+$;字段"}})
    errors = schema.verify_type(tid, {"x": "lowercase"})
    assert any("pattern" in e for e in errors)


def test_verify_pattern_passes(schema: Schema) -> None:
    """Value matching @pattern should pass."""
    tid = schema.create_type({"__self": {"x": "string;@pattern=^[A-Z]+$;字段"}})
    assert schema.verify_type(tid, {"x": "UPPER"}) == []


def test_verify_string_type_wrong(schema: Schema) -> None:
    """String __self rejects non-string data."""
    tid = schema.create_type({"__self": "string;;描述"})
    errors = schema.verify_type(tid, 123)
    assert any("string" in e for e in errors)


def test_verify_array_item_wrong_type(schema: Schema) -> None:
    """Detect wrong item type inside an array."""
    tid = schema.create_type({"__self": ["number;@required;数字"]})
    errors = schema.verify_type(tid, [1, "two", 3])
    assert any("number" in e for e in errors)


def test_verify_array_non_list(schema: Schema) -> None:
    """Detect non-list value for an array __self."""
    tid = schema.create_type({"__self": ["string;;标签"]})
    errors = schema.verify_type(tid, "not-a-list")
    assert any("array" in e for e in errors)


# ---------------------------------------------------------------------------
# verify_type — nested objects
# ---------------------------------------------------------------------------


def test_verify_nested_valid(schema: Schema) -> None:
    """Valid nested object passes."""
    tid = schema.create_type({
        "__self": {
            "ssl": {
                "enabled": "bool;;启用",
                "cert": "string;@required;证书",
            },
        },
    })
    errors = schema.verify_type(tid, {
        "ssl": {"enabled": True, "cert": "/path/to/cert"},
    })
    assert errors == []


def test_verify_nested_required_missing(schema: Schema) -> None:
    """Detect missing required field inside nested object."""
    tid = schema.create_type({
        "__self": {"ssl": {"cert": "string;@required;证书"}},
    })
    errors = schema.verify_type(tid, {"ssl": {}})
    assert any("required" in e for e in errors)


def test_verify_nested_wrong_type(schema: Schema) -> None:
    """Detect non-dict value for a nested object field."""
    tid = schema.create_type({
        "__self": {"ssl": {"enabled": "bool;;启用"}},
    })
    errors = schema.verify_type(tid, {"ssl": "not-an-object"})
    assert any("object" in e for e in errors)


# ---------------------------------------------------------------------------
# verify_type — @.Name (inline link / __typedefs)
# ---------------------------------------------------------------------------


def test_verify_inline_ref_valid(schema: Schema) -> None:
    """@.Name resolves to __typedefs and validates correctly."""
    tid = schema.create_type({
        "__self": {"addr": "@.Address;@required;地址"},
        "__typedefs": {
            "Address": {"city": "string;@required;城市"},
        },
    })
    errors = schema.verify_type(tid, {"addr": {"city": "Beijing"}})
    assert errors == []


def test_verify_inline_ref_nested_error(schema: Schema) -> None:
    """Error in data referencing a __typedefs entry is reported."""
    tid = schema.create_type({
        "__self": {"addr": "@.Address;@required;地址"},
        "__typedefs": {
            "Address": {"city": "string;@required;城市"},
        },
    })
    errors = schema.verify_type(tid, {"addr": {}})
    assert any("required" in e for e in errors)


def test_verify_inline_ref_not_found(schema: Schema) -> None:
    """Missing __typedefs entry is reported."""
    tid = schema.create_type({
        "__self": {"addr": "@.Missing;@required;地址"},
    })
    errors = schema.verify_type(tid, {"addr": {}})
    assert any("not found" in e for e in errors)


# ---------------------------------------------------------------------------
# verify_type — @TYPE-{ID} (external __self ref)
# ---------------------------------------------------------------------------


def test_verify_external_self_valid(schema: Schema) -> None:
    """@TYPE-{ID} resolves to the target's __self."""
    target_id = schema.create_type({
        "__self": {"host": "string;@required;主机"},
    })
    tid = schema.create_type({
        "__self": {"config": f"@{target_id};@required;配置"},
    })
    errors = schema.verify_type(tid, {"config": {"host": "localhost"}})
    assert errors == []


def test_verify_external_self_not_found(schema: Schema) -> None:
    """@TYPE-{ID} reports error when target doesn't exist."""
    tid = schema.create_type({
        "__self": {"x": "@TYPE-nonexistent;@required;字段"},
    })
    errors = schema.verify_type(tid, {"x": {}})
    assert any("not found" in e for e in errors)


# ---------------------------------------------------------------------------
# verify_type — @TYPE-{ID}.{name} (external __typedefs ref)
# ---------------------------------------------------------------------------


def test_verify_external_typedef_valid(schema: Schema) -> None:
    """@TYPE-{ID}.{name} resolves to the target's __typedefs entry."""
    target_id = schema.create_type({
        "__self": "string;;占位",
        "__typedefs": {
            "DatabaseConfig": {"host": "string;@required;主机"},
        },
    })
    tid = schema.create_type({
        "__self": {"db": f"@{target_id}.DatabaseConfig;@required;数据库"},
    })
    errors = schema.verify_type(tid, {"db": {"host": "localhost"}})
    assert errors == []


def test_verify_external_typedef_not_found(schema: Schema) -> None:
    """@TYPE-{ID}.{name} reports error when typedef entry is missing."""
    target_id = schema.create_type({"__self": "string;;占位"})
    tid = schema.create_type({
        "__self": {"db": f"@{target_id}.Missing;@required;数据库"},
    })
    errors = schema.verify_type(tid, {"db": {}})
    assert any("not found" in e.lower() or "Missing" in e for e in errors)


def test_verify_external_ref_non_dict(schema: Schema) -> None:
    """Non-dict value for an object type reference is rejected."""
    target_id = schema.create_type({
        "__self": {"city": "string;;城市"},
    })
    tid = schema.create_type({
        "__self": {"addr": f"@{target_id};;地址"},
    })
    errors = schema.verify_type(tid, {"addr": "not-a-dict"})
    assert any("object" in e for e in errors)


# ---------------------------------------------------------------------------
# verify_type — name parameter (__typedefs entry)
# ---------------------------------------------------------------------------


def test_verify_name_valid(schema: Schema) -> None:
    """Verify data against a named __typedefs entry."""
    tid = schema.create_type({
        "__self": "string;;占位",
        "__typedefs": {
            "Server": {"host": "string;@required;主机", "port": "number;;端口"},
        },
    })
    errors = schema.verify_type(tid, {"host": "localhost", "port": 8080}, name="Server")
    assert errors == []


def test_verify_name_error(schema: Schema) -> None:
    """Detect invalid data when verifying a named __typedefs entry."""
    tid = schema.create_type({
        "__self": "string;;占位",
        "__typedefs": {
            "Server": {"host": "string;@required;主机"},
        },
    })
    errors = schema.verify_type(tid, {}, name="Server")
    assert any("required" in e for e in errors)


def test_verify_name_not_found(schema: Schema) -> None:
    """Report error when the named __typedefs entry does not exist."""
    tid = schema.create_type({"__self": "string;;占位"})
    errors = schema.verify_type(tid, {}, name="Missing")
    assert any("not found" in e for e in errors)


def test_verify_name_type_not_found(schema: Schema) -> None:
    """Report error when type_id itself does not exist."""
    errors = schema.verify_type("TYPE-99999", {}, name="Foo")
    assert any("not found" in e for e in errors)
