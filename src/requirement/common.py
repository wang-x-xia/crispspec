"""Shared enums and exceptions for artifact managers.

A business concept is mapped onto the technical artifacts that realise
it.  The mapping is a list, not a set of fixed slots: one concept may be
realised by an entity, an interface and a role at the same time, and it
may be realised by a role that was defined long before the concept
existed.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "ALLOWED_ARTIFACT_TYPES",
    "ArtifactType",
    "CrispSpecError",
    "InvalidArtifactTypeError",
    "InvalidBusinessConceptError",
    "MappingAlreadyExistsError",
    "NotFoundError",
]


class ArtifactType(Enum):
    """The kinds of technical artifacts a business concept can map to."""

    ROLE = "ROLE"
    MODULE = "MODULE"
    ENTITY = "ENTITY"
    INTERFACE = "INTERFACE"
    ORCHESTRATION = "ORCHESTRATION"
    REACTION = "REACTION"
    SCHEDULE = "SCHEDULE"
    EVENT = "EVENT"
    ENTITY_FIELD = "ENTITY_FIELD"
    STATE_CHANGE = "STATE_CHANGE"
    INTERFACE_RESPONSE = "INTERFACE_RESPONSE"
    SIDE_EFFECT = "SIDE_EFFECT"
    ERROR = "ERROR"


#: The artifact types a business concept may be mapped to.
ALLOWED_ARTIFACT_TYPES: frozenset[ArtifactType] = frozenset(
    {
        ArtifactType.ROLE,
        ArtifactType.MODULE,
        ArtifactType.ENTITY,
        ArtifactType.INTERFACE,
        ArtifactType.ORCHESTRATION,
        ArtifactType.REACTION,
        ArtifactType.SCHEDULE,
        ArtifactType.EVENT,
        ArtifactType.ERROR,
        ArtifactType.ENTITY_FIELD,
        ArtifactType.STATE_CHANGE,
        ArtifactType.INTERFACE_RESPONSE,
        ArtifactType.SIDE_EFFECT,
    },
)


class CrispSpecError(Exception):
    """Base class for all CrispSpec domain errors."""


class NotFoundError(CrispSpecError):
    """Raised when a business concept ID does not exist."""


class MappingAlreadyExistsError(CrispSpecError):
    """Raised when a business concept already maps to the same artifact."""


class InvalidArtifactTypeError(CrispSpecError):
    """Raised when the artifact type is not allowed for a mapping."""


class InvalidBusinessConceptError(CrispSpecError):
    """Raised when a business concept fails validation."""
