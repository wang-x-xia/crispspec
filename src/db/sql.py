"""Pre-defined SQL queries for each record type."""

from .mapping import get_all_types


def _build_sqls() -> dict[str, dict[str, str]]:
    """Build SQL queries for all valid types."""
    sqls = {}
    for type_name in get_all_types():
        table = f'"t_{type_name}"'
        sqls[type_name] = {
            "create": f"CREATE TABLE IF NOT EXISTS {table} ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "data TEXT NOT NULL, "
                "version TEXT NOT NULL)",
            "select": f"SELECT id, data, version FROM {table} WHERE id = ?",
            "select_all": f"SELECT id, data, version FROM {table}",
            "insert": f"INSERT INTO {table} (data, version) VALUES (?, ?)",
            "update": f"UPDATE {table} SET data = ?, version = ? WHERE id = ? AND version = ?",
            "delete": f"DELETE FROM {table} WHERE id = ? AND version = ?",
        }
    return sqls


TYPE_SQL = _build_sqls()
