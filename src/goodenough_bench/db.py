"""SQLite connection helpers with enforced foreign-key semantics."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_sqlite(database: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled and verified."""
    connection = sqlite3.connect(str(database))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys_enabled is None or foreign_keys_enabled[0] != 1:
        connection.close()
        raise RuntimeError("SQLite foreign key enforcement could not be enabled")
    return connection


def connect_sqlite_readonly(database: str | Path) -> sqlite3.Connection:
    """Open a read-only SQLite connection with foreign keys enabled."""
    path = Path(database).resolve()
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys_enabled is None or foreign_keys_enabled[0] != 1:
        connection.close()
        raise RuntimeError("SQLite foreign key enforcement could not be enabled")
    return connection
