"""SQLite-backed implementation of :class:`IBusinessConceptStorage`.

The generic record storage (:mod:`src.db`) owns ID assignment and YAML
serialisation; this layer maps between that record-oriented view and the
business concept domain object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from src.db.types import business_concept as business_concept_type
from src.requirement.business_concept import (
    BusinessConcept,
    IBusinessConceptStorage,
    Mapping,
)
from src.requirement.common import (
    ALLOWED_ARTIFACT_TYPES,
    ArtifactType,
    InvalidArtifactTypeError,
    InvalidBusinessConceptError,
    MappingAlreadyExistsError,
    NotFoundError,
)

if TYPE_CHECKING:
    from src.db.interface import Record, Storage

__all__ = ["BusinessConceptStorage"]

_NAME_MAX_LEN = 80
_DESC_MAX_LEN = 200

#: Fields that :meth:`BusinessConceptStorage.update` is allowed to change.
_UPDATABLE_FIELDS = frozenset({"name", "description", "defined"})


class BusinessConceptStorage(IBusinessConceptStorage):
    """Business concept repository backed by the generic record storage."""

    def __init__(self, storage: Storage) -> None:
        """Initialize with the given *storage* backend."""
        self._storage = storage

    # -- reads --------------------------------------------------------------

    def get_by_id(self, record_id: str) -> BusinessConcept | None:
        """Return the concept with the given ID, or ``None`` if unknown."""
        record = self._storage.get_by_id(record_id)
        if record is None:
            return None
        return _to_domain(yaml.safe_load(record.data), record.id)

    def get_by_name(self, name: str) -> BusinessConcept | None:
        """Return the concept with the given name, or ``None`` if unknown."""
        for bc in self.list_all():
            if bc.name == name:
                return bc
        return None

    def list_all(self) -> list[BusinessConcept]:
        """Return every stored business concept."""
        records = self._storage.list_by_type(business_concept_type)
        return [_to_domain(yaml.safe_load(r.data), r.id) for r in records]

    # -- writes -------------------------------------------------------------

    def create(self, bc: BusinessConcept) -> BusinessConcept:
        """Persist a new business concept and assign it an ID.

        Args:
            bc: The concept to persist.  Its ``mappings`` are stored as-is;
                the design deliberately creates a concept before its
                mappings are known.

        Returns:
            The same concept, with ``id`` set to the canonical ID assigned
            by the storage layer.

        Raises:
            InvalidBusinessConceptError: If the concept fails validation.

        """
        _validate(bc)
        payload = _to_payload(bc)
        record = self._storage.create(
            business_concept_type,
            yaml.dump(payload, allow_unicode=True, default_flow_style=False),
        )
        bc.id = record.id
        self._save(record, bc)
        return bc

    def add_mapping(
        self,
        record_id: str,
        artifact_type: str,
        artifact_id: str,
    ) -> BusinessConcept:
        """Map the concept onto another technical artifact.

        A concept may be mapped onto as many artifacts as it needs; only
        the exact same target twice is rejected.

        Args:
            record_id: ID of the business concept.
            artifact_type: The kind of artifact being mapped, e.g.
                ``"ENTITY"``.
            artifact_id: The ID of the mapped artifact.

        Returns:
            The updated business concept.

        Raises:
            NotFoundError: If no business concept has the given ID.
            InvalidArtifactTypeError: If *artifact_type* is not one a
                business concept may be mapped to.
            MappingAlreadyExistsError: If the concept already maps to the
                same artifact.

        """
        kind = _parse_artifact_type(artifact_type)
        if kind not in ALLOWED_ARTIFACT_TYPES:
            allowed = ", ".join(sorted(a.value for a in ALLOWED_ARTIFACT_TYPES))
            msg = f"Artifact type '{kind.value}' cannot be mapped (allowed: {allowed})"
            raise InvalidArtifactTypeError(msg)

        record, bc = self._load(record_id)
        if any(
            mapping.artifact_type == kind and mapping.artifact_id == artifact_id
            for mapping in bc.mappings
        ):
            msg = (
                f"'{kind.value} {artifact_id}' is already mapped "
                f"for business concept '{record_id}'"
            )
            raise MappingAlreadyExistsError(msg)

        bc.mappings.append(Mapping(artifact_type=kind, artifact_id=artifact_id))
        self._save(record, bc)
        return bc

    def update(self, record_id: str, **fields: object) -> BusinessConcept | None:
        """Update the non-mapping fields of a concept.

        Args:
            record_id: ID of the business concept.
            **fields: Any of ``name``, ``description`` or ``defined``.

        Returns:
            The updated concept, or ``None`` if no concept has that ID.

        Raises:
            InvalidBusinessConceptError: If an unknown field is given, or the
                resulting concept fails validation.

        """
        unknown = set(fields) - _UPDATABLE_FIELDS
        if unknown:
            allowed = ", ".join(sorted(_UPDATABLE_FIELDS))
            msg = (
                f"Cannot update field(s): {', '.join(sorted(unknown))} "
                f"(allowed: {allowed})"
            )
            raise InvalidBusinessConceptError(msg)

        record = self._storage.get_by_id(record_id)
        if record is None:
            return None
        bc = _to_domain(yaml.safe_load(record.data), record.id)

        for key, value in fields.items():
            setattr(bc, key, value)
        _validate(bc)
        self._save(record, bc)
        return bc

    # -- internals ----------------------------------------------------------

    def _load(self, record_id: str) -> tuple[Record, BusinessConcept]:
        """Load the record and domain object for *record_id*.

        Raises:
            NotFoundError: If no business concept has the given ID.

        """
        record = self._storage.get_by_id(record_id)
        if record is None:
            msg = f"Business concept not found: {record_id}"
            raise NotFoundError(msg)
        return record, _to_domain(yaml.safe_load(record.data), record.id)

    def _save(self, record: Record, bc: BusinessConcept) -> None:
        """Write *bc* back to its record."""
        payload = _to_payload(bc)
        self._storage.replace(
            record.id,
            yaml.dump(payload, allow_unicode=True, default_flow_style=False),
            record.version,
        )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _to_payload(bc: BusinessConcept) -> dict[str, Any]:
    """Serialize a business concept into a YAML-friendly dict."""
    return {
        "id": bc.id,
        "name": bc.name,
        "description": bc.description,
        "defined": bc.defined,
        "as": [
            {
                "artifact_type": mapping.artifact_type.value,
                "artifact_id": mapping.artifact_id,
            }
            for mapping in bc.mappings
        ],
    }


def _to_domain(raw: dict[str, Any], record_id: str) -> BusinessConcept:
    """Deserialize a stored dict into a :class:`BusinessConcept`."""
    mappings = [
        Mapping(
            artifact_type=ArtifactType(mapping["artifact_type"]),
            artifact_id=mapping["artifact_id"],
        )
        for mapping in (raw.get("as") or [])
    ]
    return BusinessConcept(
        id=raw.get("id") or record_id,
        name=raw.get("name", ""),
        description=raw.get("description", ""),
        defined=bool(raw.get("defined", False)),
        mappings=mappings,
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate(bc: BusinessConcept) -> None:
    """Validate a business concept.

    Raises:
        InvalidBusinessConceptError: If the concept fails validation.

    """
    if not bc.name:
        msg = "name: must not be empty"
        raise InvalidBusinessConceptError(msg)
    if len(bc.name) > _NAME_MAX_LEN:
        msg = f"name: exceeds {_NAME_MAX_LEN} characters"
        raise InvalidBusinessConceptError(msg)
    if len(bc.description) > _DESC_MAX_LEN:
        msg = f"description: exceeds {_DESC_MAX_LEN} characters"
        raise InvalidBusinessConceptError(msg)


def _parse_artifact_type(value: str) -> ArtifactType:
    """Parse an artifact type name.

    Raises:
        InvalidArtifactTypeError: If *value* is not an artifact type.

    """
    try:
        return ArtifactType(value)
    except ValueError as exc:
        valid = ", ".join(a.value for a in ArtifactType)
        msg = f"Invalid artifact type: '{value}' (valid: {valid})"
        raise InvalidArtifactTypeError(msg) from exc
