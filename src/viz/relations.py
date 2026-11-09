"""The relation catalog, extracted from the artifact definition documents.

Every artifact definition (``src/<domain>/<artifact>.md``) closes with a
``## 关联`` table that declares which other artifact types it connects to
and by which edge type::

    | 方向 | 边类型 | 目标制品 |
    |------|--------|---------|
    | 出 → | `USES_TYPE` | [Entity](entity.md) |
    | ← 入 | `RETURNS` | [Interface](interface.md) |

Those tables are the single source of truth for the edges of the artifact
graph.  Rather than keeping a second, hand-maintained edge list that could
drift, this module parses them.

Two notations have to be normalised:

``出 →`` / ``← 入`` / ``出 ↔``
    *Outgoing*, *incoming* and *bidirectional*.  An incoming row is
    declared on the **target** of the edge, so it is reversed here.
``READS../../ `WRITES``
    Two relation names in one cell.  The ``../../`` is the well-known
    slash corruption documented in ``STATUS.md``; relation names are
    recovered by scanning for ``SCREAMING_SNAKE`` tokens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .catalog import PROJECT_ROOT

if TYPE_CHECKING:
    from pathlib import Path

    from .catalog import Catalog

#: Heading that introduces the relation table of a definition document.
RELATION_HEADING = "关联"

#: Direction markers used in the relation table.
_ARROW_OUT = "→"
_ARROW_IN = "←"
_ARROW_BOTH = "↔"

#: Relation names are ``SCREAMING_SNAKE`` identifiers.
_RELATION_TOKEN = re.compile(r"[A-Z][A-Z0-9_]*")

#: Markdown link inside a table cell.
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

#: Phrases that mean "every artifact type" -- expanding them would draw
#: hundreds of edges and bury the meaningful ones.
_UNIVERSAL_MARKERS = ("任意", "全部")

#: Number of columns of the relation table.
_RELATION_COLUMNS = 3


@dataclass(frozen=True)
class RelationEdge:
    """One edge of the artifact graph.

    Attributes:
        source: Type key of the edge origin.
        target: Type key of the edge destination.
        relation: The edge type, e.g. ``USES_TYPE``.
        kind: How the edge was declared -- ``out``, ``in`` or ``both``.
        origin: The definition document that declared the edge.

    """

    source: str
    target: str
    relation: str
    kind: str
    origin: str


def _section(text: str, heading: str) -> str:
    """Return the body of the ``## <heading>`` section of *text*."""
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    rest = text[start + len(marker) :]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def _relation_names(cell: str) -> list[str]:
    """Extract the relation names from a table cell.

    A cell may hold several names (``READS`` and ``WRITES``); the corrupt
    ``../../`` separator is ignored because only ``SCREAMING_SNAKE``
    tokens are picked up.
    """
    names: list[str] = []
    for token in _RELATION_TOKEN.findall(cell.replace("`", " ")):
        if token not in names:
            names.append(token)
    return names


def _direction(cell: str) -> str:
    """Classify a direction cell as ``out``, ``in`` or ``both``."""
    if _ARROW_BOTH in cell:
        return "both"
    if _ARROW_OUT in cell:
        return "out"
    if _ARROW_IN in cell:
        return "in"
    return "out"


def _resolve_link(source_file: Path, link: str) -> str | None:
    """Resolve a markdown link to a project-relative POSIX path."""
    if link.startswith(("http://", "https://", "#")):
        return None
    target = (source_file.parent / link.split("#", maxsplit=1)[0]).resolve()
    try:
        return target.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return None


def _domain_expansion(text: str, catalog: Catalog) -> list[str]:
    """Return the type keys of every domain mentioned in *text*."""
    found: list[str] = []
    for domain in catalog.domains:
        if domain.label in text or re.search(rf"\b{re.escape(domain.key)}\b", text):
            found.extend(catalog.types_in_domain(domain.key))
    return found


def parse_relation_edges(catalog: Catalog) -> tuple[RelationEdge, ...]:
    """Parse every artifact definition and collect its relation rows.

    Args:
        catalog: The artifact catalog, used to resolve the target of a
            relation to an artifact type.

    Returns:
        The de-duplicated edges of the artifact graph.

    """
    definitions = catalog.definition_map()
    edges: list[RelationEdge] = []

    for info in catalog.types:
        path = PROJECT_ROOT / info.definition
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        section = _section(text, RELATION_HEADING)
        if not section:
            continue

        for row in _table_rows(section):
            direction_cell, relation_cell, target_cell = row
            kind = _direction(direction_cell)
            names = _relation_names(relation_cell)
            targets = _resolve_targets(target_cell, path, definitions, catalog)
            if not names or not targets:
                continue

            for name in names:
                for target in targets:
                    if kind == "in":
                        source, destination = target, info.type
                    else:
                        source, destination = info.type, target
                    edges.append(
                        RelationEdge(
                            source=source,
                            target=destination,
                            relation=name,
                            kind=kind,
                            origin=info.definition,
                        ),
                    )

    return _deduplicate(edges)


def _table_rows(section: str) -> list[tuple[str, str, str]]:
    """Return the data rows of the relation table in *section*."""
    rows: list[tuple[str, str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != _RELATION_COLUMNS:
            continue
        if set(cells[1]) <= {"-", ":"} and cells[1]:
            continue  # the header separator
        if cells[0] in {"方向", "Direction"}:
            continue  # the header row
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def _resolve_targets(
    cell: str,
    source_file: Path,
    definitions: dict[str, str],
    catalog: Catalog,
) -> list[str]:
    """Resolve the target cell of a relation row to artifact type keys.

    Markdown links resolve directly.  Cells that merely name a domain
    ("契约域 / 行为域制品") expand to every type of that domain, unless
    they claim to mean *any* artifact.
    """
    targets: list[str] = []

    for _label, link in _LINK.findall(cell):
        resolved = _resolve_link(source_file, link)
        if resolved is None:
            continue
        type_key = definitions.get(resolved)
        if type_key is not None and type_key not in targets:
            targets.append(type_key)

    if targets:
        return targets

    plain = _LINK.sub("", cell)
    if any(marker in plain for marker in _UNIVERSAL_MARKERS):
        return []
    expanded = _domain_expansion(plain, catalog)
    for type_key in expanded:
        if type_key not in targets:
            targets.append(type_key)
    return targets


def _deduplicate(edges: list[RelationEdge]) -> tuple[RelationEdge, ...]:
    """Collapse edges that several documents declare identically.

    The same edge is often declared twice -- once by its source
    (``出 →``) and once by its target (``← 入``).  The first declaration
    wins; later ones only refine the recorded kind.
    """
    seen: dict[tuple[str, str, str], RelationEdge] = {}
    for edge in edges:
        key = (edge.source, edge.target, edge.relation)
        existing = seen.get(key)
        if existing is None or (existing.kind != "both" and edge.kind == "both"):
            seen[key] = edge
    return tuple(seen.values())
