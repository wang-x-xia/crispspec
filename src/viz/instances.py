"""Artifact instances read from a SQLite database.

The type catalog describes *what* an artifact is; the database holds the
artifacts themselves.  This module turns a database into the second view of
the graph -- one node per stored artifact, one edge per typed reference
between them.

The database is opened read-only: the visualiser must never create tables
or otherwise modify the store it is asked to draw.
"""

from __future__ import annotations

import re
import sqlite3
from typing import TYPE_CHECKING, Any

import yaml

from src.db.mapping import PREFIX_TO_TYPE
from src.db.types import ALL_TYPES

if TYPE_CHECKING:
    from pathlib import Path

    from .catalog import ArtifactTypeInfo, Catalog

#: A typed artifact reference, e.g. ``API-12`` or ``ENT-3.user_id``.
_REF = re.compile(r"^([A-Z]+)-(\d+)(?:\..+)?$")

#: Keys that carry no information about the relation they hold.
_GENERIC_KEYS = frozenset({"artifact_id", "id", "artifact_type", "type"})

#: Canonical relation names for the fields that carry a reference.
#:
#: The field names are stable, the relation vocabulary of the definition
#: documents is not always derivable from them, so the well-known fields
#: are mapped explicitly.
FIELD_RELATIONS: dict[str, str] = {
    "actor_role_id": "ACTED_BY",
    "constraint_id": "CONSTRAINED_BY",
    "constraint_ids": "CONSTRAINED_BY",
    "interface_ids": "CONTAINS",
    "metric_id": "MEASURES",
    "module_id": "CONTAINS",
    "owner_module_id": "CONTAINS",
    "parent_id": "PARENT_OF",
    "permission_ids": "HAS_PERMISSION",
    "process_ids": "CONTAINS",
    "projects_from_id": "PROJECTS_FROM",
    "repository_id": "LOCATED_IN",
    "role_ids": "HAS_PERMISSION",
}

#: Fields that point *at* the owning module.
#:
#: The type-level graph draws containment from the module to the
#: artifact, so these edges are reversed to match.
_REVERSED_FIELDS = frozenset({"module_id", "owner_module_id"})


def _relation_for(path: tuple[str, ...]) -> str:
    """Return the relation name to draw for a reference found at *path*.

    The last meaningful segment of the path names the relation: the
    generic ``artifact_id`` / ``id`` keys carry no information, so the
    segment above them is used instead.
    """
    segments = [part for part in path if not part.isdigit()]
    while segments and segments[-1] in _GENERIC_KEYS:
        segments.pop()
    if not segments:
        return "REFERENCES"
    field = segments[-1]
    return FIELD_RELATIONS.get(field, field.upper())


def _walk(value: object, path: tuple[str, ...]) -> list[tuple[tuple[str, ...], str]]:
    """Yield every ``(path, reference)`` pair found in *value*."""
    found: list[tuple[tuple[str, ...], str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(_walk(item, (*path, str(key))))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk(item, (*path, str(index))))
    elif isinstance(value, str):
        match = _REF.match(value.strip())
        if match is not None:
            found.append((path, value.strip()))
    return found


def _node(
    record_id: str,
    type_key: str,
    data: dict[str, Any],
    info: ArtifactTypeInfo | None,
    *,
    missing: bool,
) -> dict[str, Any]:
    """Describe one artifact instance as a graph node."""
    return {
        "id": record_id,
        "name": str(data.get("name") or record_id),
        "type": type_key,
        "typeName": info.name if info else type_key,
        "domain": info.domain if info else "meta",
        "definition": info.definition if info else "",
        "description": str(data.get("description") or ""),
        "raw": data,
        "missing": missing,
    }


def _read_records(
    conn: sqlite3.Connection,
    type_map: dict[str, ArtifactTypeInfo],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Read every stored artifact of *conn*.

    Returns:
        A ``(records, nodes)`` pair: the raw records keyed by their ID,
        and the graph nodes describing them.

    """
    records: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, Any]] = []
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }

    for type_key in ALL_TYPES:
        table = f"t_{type_key}"
        if table not in tables:
            continue
        info = type_map.get(type_key)
        # The table name comes from the constant type list, never from input.
        query = f'SELECT id, data FROM "{table}"'
        for row in conn.execute(query):
            prefix = info.id_prefix if info else type_key.upper()
            record_id = f"{prefix}-{row['id']}"
            try:
                data = yaml.safe_load(row["data"]) or {}
            except yaml.YAMLError:
                continue
            if not isinstance(data, dict):
                continue
            records[record_id] = {"type": type_key, "data": data}
            nodes.append(_node(record_id, type_key, data, info, missing=False))
    return records, nodes


def _reference_edges(
    records: dict[str, dict[str, Any]],
    nodes: list[dict[str, Any]],
    type_map: dict[str, ArtifactTypeInfo],
) -> list[dict[str, Any]]:
    """Build the edges between the stored artifacts.

    A reference to an artifact that is not stored becomes a dangling
    edge: the missing artifact is added as a ghost node so the broken
    reference stays visible.
    """
    edges: list[dict[str, Any]] = []
    for record_id, record in list(records.items()):
        for path, reference in _walk(record["data"], ()):
            match = _REF.match(reference)
            if match is None:
                continue
            target_type = PREFIX_TO_TYPE.get(match.group(1))
            if target_type is None:
                continue
            target_id = f"{match.group(1)}-{match.group(2)}"
            if target_id == record_id:
                continue
            if target_id not in records:
                info = type_map.get(target_type)
                records[target_id] = {"type": target_type, "data": {}}
                nodes.append(_node(target_id, target_type, {}, info, missing=True))
            field = ".".join(part for part in path if not part.isdigit())
            source_id, destination_id = record_id, target_id
            if path and path[-1] in _REVERSED_FIELDS:
                source_id, destination_id = target_id, record_id
            edges.append(
                {
                    "source": source_id,
                    "target": destination_id,
                    "relation": _relation_for(path),
                    "bidirectional": False,
                    "field": field,
                },
            )
    return edges


def load_instances(
    db_path: Path,
    catalog: Catalog,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load every artifact stored in *db_path*.

    Args:
        db_path: Path to the SQLite database.
        catalog: The artifact catalog, used to attach domain and
            definition information to each node.

    Returns:
        A ``(nodes, edges)`` pair of JSON-friendly dictionaries.

    """
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    if not db_path.is_file():
        return nodes, edges

    type_map = catalog.type_map()
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        records, nodes = _read_records(conn, type_map)
        edges = _reference_edges(records, nodes, type_map)
    finally:
        conn.close()

    return nodes, edges
