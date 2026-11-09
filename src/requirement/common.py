"""Shared enums and exceptions for artifact managers.

The semantic positions and artifact types defined here are reused by every
artifact that aligns business meaning with technical artifacts.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "ALLOWED_ARTIFACT_TYPES",
    "ArtifactType",
    "CrispSpecError",
    "InvalidArtifactTypeError",
    "InvalidBusinessConceptError",
    "InvalidMappingTypeError",
    "MappingAlreadyExistsError",
    "MappingType",
    "NotFoundError",
]


class MappingType(Enum):
    """The seven semantic positions a business concept can occupy."""

    AS_ACTOR = "as_actor"
    AS_OBJECT = "as_object"
    AS_ACTION = "as_action"
    AS_EVENT = "as_event"
    AS_ATTRIBUTE = "as_attribute"
    AS_RESULT = "as_result"
    AS_ERROR = "as_error"


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


#: The artifact types each semantic position accepts.
ALLOWED_ARTIFACT_TYPES: dict[MappingType, frozenset[ArtifactType]] = {
    MappingType.AS_ACTOR: frozenset({ArtifactType.ROLE, ArtifactType.MODULE}),
    MappingType.AS_OBJECT: frozenset({ArtifactType.ENTITY}),
    MappingType.AS_ACTION: frozenset({
        ArtifactType.INTERFACE,
        ArtifactType.ORCHESTRATION,
        ArtifactType.REACTION,
        ArtifactType.SCHEDULE,
    }),
    MappingType.AS_EVENT: frozenset({ArtifactType.EVENT}),
    MappingType.AS_ATTRIBUTE: frozenset({ArtifactType.ENTITY_FIELD}),
    MappingType.AS_RESULT: frozenset({
        ArtifactType.STATE_CHANGE,
        ArtifactType.INTERFACE_RESPONSE,
        ArtifactType.EVENT,
        ArtifactType.SIDE_EFFECT,
    }),
    MappingType.AS_ERROR: frozenset({ArtifactType.ERROR}),
}


class CrispSpecError(Exception):
    """Base class for all CrispSpec domain errors."""


class NotFoundError(CrispSpecError):
    """Raised when a business concept ID does not exist."""


class MappingAlreadyExistsError(CrispSpecError):
    """Raised when a semantic position is mapped more than once."""


class InvalidMappingTypeError(CrispSpecError):
    """Raised when the mapping type is not one of the seven semantic positions."""


class InvalidArtifactTypeError(CrispSpecError):
    """Raised when the artifact type is not allowed for the given mapping type."""


class InvalidBusinessConceptError(CrispSpecError):
    """Raised when a business concept fails validation."""
