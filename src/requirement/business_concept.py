"""Business Concept artifact model and storage interface.

A business concept is the bridge between product language and technical
artifacts: it names a concept the business talks about and records which
technical artifact realises it in each semantic position.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.requirement.common import ArtifactType, MappingType

__all__ = [
    "BusinessConcept",
    "IBusinessConceptStorage",
    "Mapping",
]


@dataclass(frozen=True)
class Mapping:
    """A mapping from one semantic position to a technical artifact."""

    artifact_type: ArtifactType
    artifact_id: str


@dataclass
class BusinessConcept:
    """A business concept and its alignment with technical artifacts.

    ``id`` is assigned by the storage layer on creation — it is empty until
    the concept has been persisted.
    """

    id: str = ""
    name: str = ""
    description: str = ""
    defined: bool = False
    mappings: dict[MappingType, Mapping] = field(default_factory=dict)


class IBusinessConceptStorage(ABC):
    """Persistence interface for business concepts."""

    @abstractmethod
    def get_by_id(self, record_id: str) -> BusinessConcept | None:
        """Return the concept with the given ID, or ``None`` if unknown."""
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> BusinessConcept | None:
        """Return the concept with the given name, or ``None`` if unknown."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[BusinessConcept]:
        """Return every stored business concept."""
        raise NotImplementedError

    @abstractmethod
    def create(self, bc: BusinessConcept) -> BusinessConcept:
        """Persist a new business concept and assign it an ID."""
        raise NotImplementedError

    @abstractmethod
    def add_mapping(
        self,
        record_id: str,
        mapping_type: str,
        artifact_type: str,
        artifact_id: str,
    ) -> BusinessConcept:
        """Map a semantic position to a technical artifact."""
        raise NotImplementedError

    @abstractmethod
    def update(self, record_id: str, **fields: object) -> BusinessConcept | None:
        """Update the non-mapping fields of a concept."""
        raise NotImplementedError
