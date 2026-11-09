"""The artifact type catalog.

``artifacts.yaml`` is the machine-readable registry of every artifact type
the system knows about: 35 entries, each with its ID prefix, domain,
definition file, implementation status and Stage.  This module turns that
registry into typed, immutable data structures that the graph builder can
consume without re-parsing YAML all over the place.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "artifacts.yaml"

#: Domain keys that are not artifact domains but still worth showing.
META_DOMAIN = "meta"


@dataclass(frozen=True)
class DomainInfo:
    """A domain -- a concern that groups related artifact types."""

    key: str
    label: str
    question: str


@dataclass(frozen=True)
class ArtifactTypeInfo:
    """One artifact type, as registered in ``artifacts.yaml``."""

    type: str
    name: str
    id_prefix: str
    domain: str
    definition: str
    manager: str | None
    tests: str | None
    status: str
    stage: int
    priority: str
    depends_on: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class Catalog:
    """Every artifact type and domain the project knows about."""

    types: tuple[ArtifactTypeInfo, ...]
    domains: tuple[DomainInfo, ...]

    def type_map(self) -> dict[str, ArtifactTypeInfo]:
        """Return the artifact types keyed by their type key."""
        return {info.type: info for info in self.types}

    def domain_map(self) -> dict[str, DomainInfo]:
        """Return the domains keyed by their domain key."""
        return {domain.key: domain for domain in self.domains}

    def definition_map(self) -> dict[str, str]:
        r"""Return a mapping of definition file path to artifact type key.

        Paths are normalised to POSIX form and relative to the project
        root, so ``src\contract\entity.md`` and ``src/contract/entity.md``
        both resolve to the same key.
        """
        return {info.definition.replace("\\", "/"): info.type for info in self.types}

    def types_in_domain(self, domain_key: str) -> tuple[str, ...]:
        """Return the type keys belonging to *domain_key*."""
        return tuple(info.type for info in self.types if info.domain == domain_key)


def _one_line(text: str) -> str:
    """Flatten *text* into a single line, keeping the words readable."""
    return " ".join(text.split())


def load_catalog(registry_path: Path | None = None) -> Catalog:
    """Load the artifact catalog from ``artifacts.yaml``.

    Args:
        registry_path: Path to the registry file.  Defaults to the
            repository's ``artifacts.yaml``.

    Returns:
        The loaded :class:`Catalog`.

    Raises:
        ValueError: If the registry file is missing or malformed.

    """
    path = registry_path or REGISTRY_PATH
    if not path.is_file():
        msg = f"Artifact registry not found: {path}"
        raise ValueError(msg)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"Artifact registry must be a mapping: {path}"
        raise TypeError(msg)

    domains: list[DomainInfo] = []
    for key, value in (raw.get("domains") or {}).items():
        domains.append(
            DomainInfo(
                key=key,
                label=str(value.get("label", key)),
                question=_one_line(str(value.get("question", ""))),
            ),
        )

    types: list[ArtifactTypeInfo] = [
        ArtifactTypeInfo(
            type=str(entry["type"]),
            name=str(entry["name"]),
            id_prefix=str(entry["id_prefix"]),
            domain=str(entry["domain"]),
            definition=str(entry["definition"]).replace("\\", "/"),
            manager=entry.get("manager"),
            tests=entry.get("tests"),
            status=str(entry.get("status", "not-started")),
            stage=int(entry.get("stage", 1)),
            priority=str(entry.get("priority", "P0")),
            depends_on=tuple(entry.get("depends_on") or ()),
            notes=_one_line(str(entry.get("notes") or "")),
        )
        for entry in raw.get("artifacts") or []
    ]

    return Catalog(types=tuple(types), domains=tuple(domains))
