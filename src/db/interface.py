"""Database interfaces for crispsec project."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Record:
    """A record stored in the database."""

    id: str
    type: str
    data: str
    version: str


class Storage(ABC):
    """Abstract storage interface."""

    @abstractmethod
    def get_by_id(self, record_id: str) -> Record | None:
        """Retrieve a record by its ID."""
        raise NotImplementedError

    @abstractmethod
    def list_by_type(self, record_type: str) -> list[Record]:
        """List all records of a given type."""
        raise NotImplementedError

    @abstractmethod
    def create(self, record_type: str, data: str) -> Record:
        """Create a new record."""
        raise NotImplementedError

    @abstractmethod
    def replace(self, record_id: str, data: str, version: str) -> bool:
        """Replace an existing record."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, record_id: str, version: str) -> bool:
        """Delete a record."""
        raise NotImplementedError
