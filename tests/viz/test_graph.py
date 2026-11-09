"""Tests for the artifact catalog, the relation parser and the page.

The visualiser is only useful if it reflects the repository it is built
from, so most of these tests assert that the parsed graph agrees with the
documents and the registry that describe it.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import pytest

from src.db.types import ALL_TYPES
from src.viz.build import build, render_for
from src.viz.catalog import PROJECT_ROOT, Catalog, load_catalog
from src.viz.fields import TypeDetails, parse_type_details
from src.viz.graph import build_payload
from src.viz.relations import RelationEdge, _relation_names, parse_relation_edges
from src.viz.render import PLACEHOLDER, render_page

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    """Return the artifact catalog."""
    return load_catalog()


@pytest.fixture(scope="module")
def edges(catalog: Catalog) -> tuple[RelationEdge, ...]:
    """Return the parsed relation edges."""
    return parse_relation_edges(catalog)


@pytest.fixture(scope="module")
def details(catalog: Catalog) -> dict[str, TypeDetails]:
    """Return the parsed field and enum details."""
    return parse_type_details(catalog)


@pytest.fixture(scope="module")
def payload(catalog: Catalog) -> dict[str, Any]:
    """Return the complete graph payload."""
    return build_payload(catalog)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_catalog_covers_every_registered_type(catalog: Catalog) -> None:
    """The catalog holds one entry per type known to the code."""
    assert sorted(info.type for info in catalog.types) == sorted(ALL_TYPES)


def test_catalog_domains_are_declared(catalog: Catalog) -> None:
    """Every artifact belongs to a declared domain."""
    declared = {domain.key for domain in catalog.domains}
    for info in catalog.types:
        assert info.domain in declared


def test_definition_map_resolves_relative_paths(catalog: Catalog) -> None:
    """A definition path maps to the artifact type that owns it."""
    definitions = catalog.definition_map()
    assert definitions["src/contract/entity.md"] == "entity"
    assert definitions["src/module/module.md"] == "module"


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


def test_relation_edges_connect_known_types(
    catalog: Catalog,
    edges: tuple[RelationEdge, ...],
) -> None:
    """Every edge points at an artifact type that exists."""
    known = {info.type for info in catalog.types}
    for edge in edges:
        assert edge.source in known, edge
        assert edge.target in known, edge


def test_relation_edges_are_unique(edges: tuple[RelationEdge, ...]) -> None:
    """The same edge is never drawn twice."""
    keys = [(edge.source, edge.target, edge.relation) for edge in edges]
    assert len(keys) == len(set(keys))


def test_outgoing_rows_become_outgoing_edges(edges: tuple[RelationEdge, ...]) -> None:
    """A row declared as outgoing points away from the declaring artifact."""
    pairs = {(edge.source, edge.target, edge.relation) for edge in edges}
    assert ("interface", "entity", "USES_TYPE") in pairs
    assert ("interface", "error", "RETURNS") in pairs
    assert ("orchestration", "interface", "COMPOSES") in pairs


def test_incoming_rows_are_reversed(edges: tuple[RelationEdge, ...]) -> None:
    """A row declared as incoming is stored the other way round."""
    pairs = {(edge.source, edge.target, edge.relation) for edge in edges}
    # Interface declares "出 → RETURNS Error", Error declares "← 入 RETURNS Interface".
    assert ("interface", "error", "RETURNS") in pairs
    assert ("error", "interface", "RETURNS") not in pairs


def test_self_reference_is_bidirectional(edges: tuple[RelationEdge, ...]) -> None:
    """A "出 ↔" row produces a bidirectional edge."""
    module_edges = [
        edge
        for edge in edges
        if edge.source == "module"
        and edge.target == "module"
        and edge.relation == "DEPENDS_ON"
    ]
    assert len(module_edges) == 1
    assert module_edges[0].kind == "both"


def test_multiple_relations_in_one_cell_are_split() -> None:
    """A cell that holds several relation names yields several relations.

    The definitions used to spell this ``READS../../ `WRITES`` -- the
    slash corruption of STATUS.md §6.8 -- and the parser still has to
    cope with it wherever it shows up.
    """
    assert _relation_names("`READS../../ `WRITES`") == ["READS", "WRITES"]
    assert _relation_names("`CONTAINS`") == ["CONTAINS"]
    assert _relation_names("`A` / `B`") == ["A", "B"]


def test_domain_targets_are_expanded(edges: tuple[RelationEdge, ...]) -> None:
    """A target cell naming a domain expands to the types of that domain."""
    targets = {
        edge.target
        for edge in edges
        if edge.source == "code-ref" and edge.relation == "IMPLEMENTS"
    }
    assert "entity" in targets
    assert "interface" in targets
    assert "process" in targets


# ---------------------------------------------------------------------------
# Fields and enums
# ---------------------------------------------------------------------------


def test_every_type_has_details(details: dict[str, TypeDetails]) -> None:
    """Each artifact type is described."""
    assert set(details) == set(ALL_TYPES)


def test_fields_are_parsed(details: dict[str, TypeDetails]) -> None:
    """The field table of a definition becomes fields."""
    interface = details["interface"]
    names = [field.name for field in interface.fields]
    assert "id" in names
    assert "module_id" in names
    assert "error_ids" in names


def test_enums_are_parsed(details: dict[str, TypeDetails]) -> None:
    """The enum tables of a definition become value sets."""
    role = details["role"]
    assert role.enums
    values = [value for enum in role.enums for value, _ in enum.values]
    assert "HUMAN" in values or "SERVICE" in values


def test_business_concept_mappings_are_parsed(details: dict[str, TypeDetails]) -> None:
    """The ``as`` mapping of the Business Concept is read."""
    mappings = details["business-concept"].mappings
    assert mappings
    assert {mapping.artifact_type for mapping in mappings} == {
        "ENTITY",
        "INTERFACE",
        "ROLE",
    }


def test_slash_corruption_is_repaired(details: dict[str, TypeDetails]) -> None:
    """The ``../../`` corruption of the documents does not reach the page."""
    interface = details["interface"]
    for field in interface.fields:
        assert "../../" not in field.constraint
        assert "../../" not in field.description


# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------


def test_payload_has_the_expected_shape(payload: dict[str, Any]) -> None:
    """The payload carries the nodes, the edges and the domains."""
    assert set(payload) >= {"domains", "types", "edges", "relationTypes", "instances"}
    assert len(payload["types"]) == len(ALL_TYPES)
    assert payload["edges"]
    assert payload["domains"]


def test_payload_edges_reference_known_types(payload: dict[str, Any]) -> None:
    """No edge dangles in the payload."""
    known = {node["id"] for node in payload["types"]}
    for edge in payload["edges"]:
        assert edge["source"] in known
        assert edge["target"] in known


def test_payload_contains_business_concept_mapping_edges(payload: dict[str, Any]) -> None:
    """The business concept maps onto the internal artifacts."""
    relations = {
        edge["relation"] for edge in payload["edges"] if edge["source"] == "business-concept"
    }
    assert relations == {"AS"}
    targets = {
        edge["target"] for edge in payload["edges"] if edge["source"] == "business-concept"
    }
    assert {"entity", "interface", "role", "error", "event"} <= targets


def test_payload_relation_types_are_counted(payload: dict[str, Any]) -> None:
    """Every relation type of the payload is counted."""
    counts = {item["name"]: item["count"] for item in payload["relationTypes"]}
    assert counts["USES_TYPE"] >= 1
    assert sum(counts.values()) == len(payload["edges"])


def test_payload_is_json_serialisable(payload: dict[str, Any]) -> None:
    """The payload survives a round trip through JSON."""
    assert json.loads(json.dumps(payload, ensure_ascii=False))["types"]


# ---------------------------------------------------------------------------
# Development mainline
# ---------------------------------------------------------------------------


def test_payload_contains_the_mainline(payload: dict[str, Any]) -> None:
    """The payload carries the development mainline."""
    assert payload["phases"]
    covered = [name for phase in payload["phases"] for name in phase["artifacts"]]
    assert sorted(covered) == sorted(ALL_TYPES), "the mainline misses an artifact"


def test_mainline_handoffs_and_marked_edges_agree(payload: dict[str, Any]) -> None:
    """The declared hand-offs are exactly the edges flagged as mainline."""
    declared = {
        (handoff["source"], handoff["target"], handoff["relation"])
        for phase in payload["phases"]
        for handoff in phase["handoff"]
    }
    marked = {
        (edge["source"], edge["target"], edge["relation"])
        for edge in payload["edges"]
        if edge["mainline"]
    }
    assert declared == marked


def test_mainline_phases_keep_their_order(payload: dict[str, Any]) -> None:
    """The mainline runs from intent to operation, then the lateral phases."""
    ids = [phase["id"] for phase in payload["phases"]]
    assert ids[0] == "intent"
    assert ids.index("code") < ids.index("verification") < ids.index("delivery")


def test_lateral_phases_come_last(payload: dict[str, Any]) -> None:
    """The cross-cutting phases trail the spine."""
    lateral = [phase["id"] for phase in payload["phases"] if phase["lateral"]]
    assert lateral == ["governance", "access", "meta"]
    spine = [phase for phase in payload["phases"] if not phase["lateral"]]
    assert all(phase["handoff"] for phase in spine[1:]), "a spine phase has no hand-off"


def test_prepared_artifacts_are_not_produced(payload: dict[str, Any]) -> None:
    """An artifact is either produced by a phase or prepared for it, never both."""
    for phase in payload["phases"]:
        assert not set(phase["produces"]) & set(phase["prepares"]), phase["id"]
        assert set(phase["artifacts"]) == set(phase["produces"]) | set(phase["prepares"])


def test_business_concept_is_prepared_not_produced(payload: dict[str, Any]) -> None:
    """The business concept may be defined long before the flow starts."""
    phases = {phase["id"]: phase for phase in payload["phases"]}
    assert "business-concept" in phases["requirement"]["prepares"]
    assert "business-concept" not in phases["requirement"]["produces"]


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


def test_render_page_embeds_the_payload(payload: dict[str, Any]) -> None:
    """The payload is embedded in the page."""
    html = render_page(payload)
    assert PLACEHOLDER not in html
    assert '"types"' in html


def test_render_page_is_self_contained(payload: dict[str, Any]) -> None:
    """The page loads no external resource."""
    html = render_page(payload)
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    assert external == []


def test_render_page_contains_the_graph_elements(payload: dict[str, Any]) -> None:
    """The page ships the viewer itself, not a stub."""
    html = render_page(payload)
    for marker in ('<svg id="graph"', "crisp-spec-data", "buildSchemaGraph"):
        assert marker in html


def test_build_writes_a_page(tmp_path: Path) -> None:
    """The generator writes a page that embeds a valid payload."""
    output = tmp_path / "graph.html"
    build(output)
    html = output.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="crisp-spec-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    data = json.loads(match.group(1))
    assert len(data["types"]) == len(ALL_TYPES)


def test_the_committed_page_is_up_to_date(catalog: Catalog) -> None:
    """The committed page matches the documents it is built from.

    The page is generated, not written by hand; regenerating it must not
    change a single byte, otherwise the definitions and the page drifted
    apart.
    """
    committed = PROJECT_ROOT / "docs" / "artifact-graph.html"
    assert committed.is_file(), "run `uv run python -m src.viz.build`"
    assert render_for(committed, catalog) == committed.read_text(encoding="utf-8")
