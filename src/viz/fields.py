"""Field and enum details, extracted from the artifact definition documents.

The ``## 字段定义`` section of every definition document holds the field
table (name / type / constraint / description) and, below it, the enum
tables of the artifact.  The visualiser shows both in the detail panel of a
node, so the page carries the full definition of every artifact type
instead of just its name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .catalog import PROJECT_ROOT, Catalog

#: Heading that introduces the field table of a definition document.
FIELD_HEADING = "字段定义"

#: Heading of the table that maps the seven semantic positions.
MAPPING_HEADING = "七个核心映射位置"

_FIELD_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

#: Number of columns of the field table of a definition document.
FIELD_COLUMNS = 4

#: Number of columns of an enum table.
ENUM_COLUMNS = 2

#: Number of columns of the semantic position table.
MAPPING_COLUMNS = 3

#: ``key: type`` line of an inline YAML schema block.
_SCHEMA_LINE = re.compile(r"^([a-z][a-z0-9_]*):\s*(\S*)")

#: The ``../../`` slash corruption documented in ``STATUS.md`` (§6.8).
#:
#: A ``/`` that is not part of a real relative path was replaced by
#: ``../../``.  Markdown links are removed before the repair, because
#: those are the only places where a real ``../../`` path survives.
_CORRUPT_SLASH = re.compile(r"\.\./\.\./")

#: A markdown link inside a table cell.
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


@dataclass(frozen=True)
class FieldInfo:
    """One field of an artifact type."""

    name: str
    type: str
    constraint: str
    description: str


@dataclass(frozen=True)
class EnumInfo:
    """One enumerated value set of an artifact type."""

    name: str
    values: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class MappingInfo:
    """One semantic position of the Business Concept artifact."""

    position: str
    targets: str
    source_field: str


@dataclass(frozen=True)
class TypeDetails:
    """The parsed details of one artifact type."""

    fields: tuple[FieldInfo, ...] = ()
    enums: tuple[EnumInfo, ...] = ()
    mappings: tuple[MappingInfo, ...] = ()


def _clean(cell: str) -> str:
    """Strip the markdown decoration of a table cell.

    Also repairs the ``../../`` slash corruption (see ``STATUS.md`` §6.8),
    which swallowed the slashes that separate the values of an enum.
    """
    text = _LINK.sub(r"\1", cell)
    text = text.replace("`", "").replace("**", "")
    text = text.replace("\\<", "<").replace("\\>", ">")
    text = _CORRUPT_SLASH.sub("/", text)
    return text.strip()


def _tables(section: str) -> list[tuple[str, list[list[str]]]]:
    """Return the tables of *section* with the heading that precedes them.

    The heading of the first table is empty -- it belongs to the section
    itself rather than to a subsection.
    """
    result: list[tuple[str, list[list[str]]]] = []
    heading = ""
    rows: list[list[str]] = []

    def flush() -> None:
        if rows:
            result.append((heading, rows))

    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            flush()
            rows = []
            heading = stripped[4:].strip()
            continue
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":"} for cell in cells if cell):
            continue
        rows.append(cells)
    flush()
    return result


def _is_separator(row: list[str]) -> bool:
    """Tell whether *row* is a table separator such as ``|---|---|``."""
    return bool(row) and all(set(cell) <= {"-", ":"} for cell in row if cell)


def _parse_fields(rows: list[list[str]]) -> tuple[FieldInfo, ...]:
    """Parse the field table of an artifact type."""
    fields: list[FieldInfo] = []
    for row in rows[1:]:
        if len(row) < FIELD_COLUMNS or _is_separator(row):
            continue
        name = _clean(row[0])
        if not _FIELD_NAME.fullmatch(name):
            continue
        fields.append(
            FieldInfo(
                name=name,
                type=_clean(row[1]),
                constraint=_clean(row[2]),
                description=_clean(row[3]),
            ),
        )
    return tuple(fields)


def _parse_enum(heading: str, rows: list[list[str]]) -> EnumInfo | None:
    """Parse an enum table such as ``### type 枚举``."""
    values: list[tuple[str, str]] = []
    for row in rows[1:]:
        if len(row) < ENUM_COLUMNS or _is_separator(row):
            continue
        value = _clean(row[0])
        if not value:
            continue
        values.append((value, _clean(row[1])))
    if not values:
        return None
    return EnumInfo(name=heading, values=tuple(values))


def _parse_mappings(rows: list[list[str]]) -> tuple[MappingInfo, ...]:
    """Parse the seven semantic positions of the Business Concept."""
    mappings: list[MappingInfo] = []
    for row in rows[1:]:
        if len(row) < MAPPING_COLUMNS or _is_separator(row):
            continue
        position = _clean(row[0])
        if not position.startswith("as_"):
            continue
        mappings.append(
            MappingInfo(
                position=position,
                targets=_clean(row[1]),
                source_field=_clean(row[2]),
            ),
        )
    return tuple(mappings)


def _section(text: str, keyword: str) -> str:
    """Return the body of the section whose heading contains *keyword*.

    The headings are not uniform -- ``## 二、七个核心映射位置`` and
    ``## 字段定义`` -- so they are matched by content rather than by
    exact text.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("## ") or keyword not in line:
            continue
        body: list[str] = []
        for follow in lines[index + 1 :]:
            if follow.startswith("## "):
                break
            body.append(follow)
        return "\n".join(body)
    return ""


def _schema_block_fields(text: str) -> tuple[FieldInfo, ...]:
    """Parse the fields of an inline YAML schema block.

    A few definition documents describe their fields as a YAML snippet
    instead of a table; those are read here.  Only the top-level keys of
    the block are fields -- nested keys belong to a sub-structure.
    """
    fields: list[FieldInfo] = []
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_block = not in_block
            continue
        if not in_block or not line or line[0].isspace() or stripped.startswith("#"):
            continue
        match = _SCHEMA_LINE.match(stripped)
        if match is None:
            continue
        type_name = (match.group(2) or "").strip('"\'')
        fields.append(
            FieldInfo(name=match.group(1), type=type_name, constraint="", description=""),
        )
    return tuple(fields)


def parse_type_details(catalog: Catalog) -> dict[str, TypeDetails]:
    """Parse the field and enum tables of every artifact definition.

    Args:
        catalog: The artifact catalog.

    Returns:
        A mapping of artifact type key to its parsed details.

    """
    details: dict[str, TypeDetails] = {}
    for info in catalog.types:
        path = PROJECT_ROOT / info.definition
        if not path.is_file():
            details[info.type] = TypeDetails()
            continue
        text = path.read_text(encoding="utf-8")

        fields: tuple[FieldInfo, ...] = ()
        enums: list[EnumInfo] = []
        for heading, rows in _tables(_section(text, FIELD_HEADING)):
            if not rows:
                continue
            if not fields and len(rows[0]) >= FIELD_COLUMNS:
                fields = _parse_fields(rows)
                continue
            parsed = _parse_enum(heading or "枚举", rows)
            if parsed is not None:
                enums.append(parsed)
        if not fields:
            fields = _schema_block_fields(text)

        mappings: tuple[MappingInfo, ...] = ()
        for _heading, rows in _tables(_section(text, MAPPING_HEADING)):
            mappings = _parse_mappings(rows)
            break

        details[info.type] = TypeDetails(
            fields=fields,
            enums=tuple(enums),
            mappings=mappings,
        )
    return details
