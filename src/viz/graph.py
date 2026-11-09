"""Assembly of the graph payload.

Turns the catalog, the relation table and the optional artifact instances
into a single JSON-serialisable payload.  The payload is what the HTML
page consumes; nothing in it depends on Python.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.requirement.common import ALLOWED_ARTIFACT_TYPES, ArtifactType

from .fields import TypeDetails, parse_type_details
from .instances import load_instances
from .relations import RelationEdge, parse_relation_edges

if TYPE_CHECKING:
    from pathlib import Path

    from .catalog import Catalog, DomainInfo

#: Colours used for the domains, in the order the domains are declared
#: in ``artifacts.yaml``.
DOMAIN_COLORS: tuple[str, ...] = (
    "#4f9dff",  # requirement
    "#22c55e",  # contract
    "#f59e0b",  # behavior
    "#a855f7",  # code
    "#ef4444",  # incident
    "#06b6d4",  # governance
    "#f97316",  # access
    "#ec4899",  # delivery
    "#84cc16",  # verification
    "#eab308",  # organization
    "#64748b",  # meta
)

#: ``ArtifactType`` values that do not name an artifact type of their own.
_NON_TYPE_ARTIFACTS = frozenset(
    {
        ArtifactType.ENTITY_FIELD,
        ArtifactType.STATE_CHANGE,
        ArtifactType.INTERFACE_RESPONSE,
        ArtifactType.SIDE_EFFECT,
    },
)

#: ``ArtifactType`` value -> artifact type key.
_ARTIFACT_TYPE_KEYS: dict[ArtifactType, str] = {
    ArtifactType.ROLE: "role",
    ArtifactType.MODULE: "module",
    ArtifactType.ENTITY: "entity",
    ArtifactType.INTERFACE: "interface",
    ArtifactType.ORCHESTRATION: "orchestration",
    ArtifactType.REACTION: "reaction",
    ArtifactType.SCHEDULE: "schedule",
    ArtifactType.EVENT: "event",
    ArtifactType.ERROR: "error",
}


def _domain_payload(domains: tuple[DomainInfo, ...]) -> list[dict[str, Any]]:
    """Describe every domain, including its colour."""
    payload: list[dict[str, Any]] = []
    for index, domain in enumerate(domains):
        payload.append(
            {
                "key": domain.key,
                "label": domain.label,
                "question": domain.question,
                "color": DOMAIN_COLORS[index % len(DOMAIN_COLORS)],
            },
        )
    return payload


def _node_payload(
    catalog: Catalog,
    details: dict[str, TypeDetails],
) -> list[dict[str, Any]]:
    """Describe every artifact type."""
    domains = catalog.domain_map()
    nodes: list[dict[str, Any]] = []
    for info in catalog.types:
        detail = details.get(info.type, TypeDetails())
        domain = domains.get(info.domain)
        nodes.append(
            {
                "id": info.type,
                "name": info.name,
                "prefix": info.id_prefix,
                "domain": info.domain,
                "domainLabel": domain.label if domain else info.domain,
                "definition": info.definition,
                "manager": info.manager,
                "tests": info.tests,
                "status": info.status,
                "stage": info.stage,
                "priority": info.priority,
                "dependsOn": list(info.depends_on),
                "notes": info.notes,
                "fields": [
                    {
                        "name": field.name,
                        "type": field.type,
                        "constraint": field.constraint,
                        "description": field.description,
                    }
                    for field in detail.fields
                ],
                "enums": [
                    {"name": enum.name, "values": [list(value) for value in enum.values]}
                    for enum in detail.enums
                ],
                "mappings": [
                    {
                        "position": mapping.position,
                        "targets": mapping.targets,
                        "sourceField": mapping.source_field,
                    }
                    for mapping in detail.mappings
                ],
            },
        )
    return nodes


def _edge_payload(edges: tuple[RelationEdge, ...]) -> list[dict[str, Any]]:
    """Describe every edge of the artifact graph."""
    return [
        {
            "source": edge.source,
            "target": edge.target,
            "relation": edge.relation,
            "bidirectional": edge.kind == "both",
            "origin": edge.origin,
        }
        for edge in edges
    ]


def _business_concept_edges() -> list[dict[str, Any]]:
    """Build the seven semantic mapping edges of the Business Concept.

    The concepts document describes them in prose; the authoritative
    mapping lives in :data:`ALLOWED_ARTIFACT_TYPES`.
    """
    edges: list[dict[str, Any]] = []
    for position, allowed in ALLOWED_ARTIFACT_TYPES.items():
        for artifact_type in sorted(allowed, key=lambda item: item.value):
            if artifact_type in _NON_TYPE_ARTIFACTS:
                continue
            target = _ARTIFACT_TYPE_KEYS.get(artifact_type)
            if target is None:
                continue
            edges.append(
                {
                    "source": "business-concept",
                    "target": target,
                    "relation": position.value.upper(),
                    "bidirectional": False,
                    "origin": "src/requirement/common.py",
                },
            )
    return edges


def _relation_summary(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count how often each relation type occurs."""
    counts: dict[str, int] = {}
    for edge in edges:
        counts[edge["relation"]] = counts.get(edge["relation"], 0) + 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _phase_payload(catalog: Catalog) -> list[dict[str, Any]]:
    """Describe every phase of the development mainline."""
    return [
        {
            "id": phase.id,
            "label": phase.label,
            "question": phase.question,
            "produces": list(phase.produces),
            "prepares": list(phase.prepares),
            "artifacts": list(phase.artifacts),
            "lateral": phase.lateral,
            "handoff": [
                {"relation": handoff.relation, "source": handoff.source, "target": handoff.target}
                for handoff in phase.handoff
            ],
        }
        for phase in catalog.phases
    ]


def _mark_mainline(edges: list[dict[str, Any]], catalog: Catalog) -> None:
    """Flag the edges that carry the development mainline."""
    spine = {
        (handoff.source, handoff.target, handoff.relation)
        for phase in catalog.phases
        for handoff in phase.handoff
    }
    for edge in edges:
        edge["mainline"] = (edge["source"], edge["target"], edge["relation"]) in spine


def build_payload(
    catalog: Catalog,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Build the complete payload of the visualiser.

    Args:
        catalog: The artifact catalog.
        db_path: Optional path to a SQLite database holding artifact
            instances.  When given, the page also offers an instance view.

    Returns:
        A JSON-serialisable dictionary.

    """
    details = parse_type_details(catalog)
    edges = list(_edge_payload(parse_relation_edges(catalog)))
    edges.extend(_business_concept_edges())

    nodes = _node_payload(catalog, details)
    known = {node["id"] for node in nodes}
    edges = [edge for edge in edges if edge["source"] in known and edge["target"] in known]
    _mark_mainline(edges, catalog)

    instance_nodes: list[dict[str, Any]] = []
    instance_edges: list[dict[str, Any]] = []
    db_label = ""
    if db_path is not None:
        instance_nodes, instance_edges = load_instances(db_path, catalog)
        db_label = db_path.name

    return {
        "domains": _domain_payload(catalog.domains),
        "phases": _phase_payload(catalog),
        "types": nodes,
        "edges": edges,
        "relationTypes": _relation_summary(edges),
        "instances": {
            "available": bool(instance_nodes),
            "dbName": db_label,
            "nodes": instance_nodes,
            "edges": instance_edges,
        },
    }
