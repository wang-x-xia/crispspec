"""Sqlite storage implementation for crispsec project."""

from __future__ import annotations

import sqlite3
import uuid

from .interface import Record, Storage
from .mapping import generate_id, is_valid_type, prefix_to_type, type_to_prefix
from .sql import TYPE_SQL


class SqliteStorage(Storage):
    """SQLite-based storage implementation."""

    def __init__(self, db_path: str) -> None:
        """Initialize the storage with a database path."""
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def _ensure_table(self, type_name: str) -> None:
        """Ensure the table for a type exists."""
        if not is_valid_type(type_name):
            msg = f"Invalid type: {type_name}"
            raise ValueError(msg)
        self._conn.execute(TYPE_SQL[type_name]["create"])
        self._conn.commit()

    def get_by_id(self, record_id: str) -> Record | None:
        """Retrieve a record by its ID."""
        prefix, num_str = record_id.rsplit("-", 1)
        type_ = self._type_from_prefix(prefix)
        self._ensure_table(type_)
        cursor = self._conn.execute(
            TYPE_SQL[type_]["select"],
            (int(num_str),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Record(
            id=record_id,
            type=type_,
            data=row["data"],
            version=row["version"],
        )

    def list_by_type(self, record_type: str) -> list[Record]:
        """List all records of a given type."""
        self._ensure_table(record_type)
        cursor = self._conn.execute(TYPE_SQL[record_type]["select_all"])
        rows = cursor.fetchall()
        prefix = self._prefix_from_type(record_type)
        return [
            Record(
                id=f"{prefix}-{row['id']}",
                type=record_type,
                data=row["data"],
                version=row["version"],
            )
            for row in rows
        ]

    def create(self, record_type: str, data: str) -> Record:
        """Create a new record."""
        self._ensure_table(record_type)
        version = str(uuid.uuid4())
        cursor = self._conn.execute(
            TYPE_SQL[record_type]["insert"],
            (data, version),
        )
        self._conn.commit()
        auto_id = cursor.lastrowid
        id_ = generate_id(record_type, auto_id)
        return Record(id=id_, type=record_type, data=data, version=version)

    def replace(self, record_id: str, data: str, version: str) -> bool:
        """Replace an existing record."""
        prefix, num_str = record_id.rsplit("-", 1)
        type_ = self._type_from_prefix(prefix)
        self._ensure_table(type_)
        new_version = str(uuid.uuid4())
        cursor = self._conn.execute(
            TYPE_SQL[type_]["update"],
            (data, new_version, int(num_str), version),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def delete(self, record_id: str, version: str) -> bool:
        """Delete a record."""
        prefix, num_str = record_id.rsplit("-", 1)
        type_ = self._type_from_prefix(prefix)
        self._ensure_table(type_)
        cursor = self._conn.execute(
            TYPE_SQL[type_]["delete"],
            (int(num_str), version),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def _type_from_prefix(self, prefix: str) -> str:
        """Get the type from a prefix."""
        return prefix_to_type(prefix)

    def _prefix_from_type(self, type_name: str) -> str:
        """Get the prefix from a type."""
        return type_to_prefix(type_name)
