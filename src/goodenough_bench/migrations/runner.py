"""Tracked SQLite schema migrations."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Iterable

from goodenough_bench.db import connect_sqlite
from goodenough_bench.exceptions import MigrationError

MIGRATION_PATTERN = re.compile(r"^(\d{4})_(.+)\.sql$")


@dataclass(frozen=True)
class Migration:
    version: int
    filename: str
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def discover_migrations(
    *,
    package: str = "goodenough_bench.migrations",
) -> list[Migration]:
    """Discover packaged SQL migrations in deterministic version order."""
    migrations_by_version: dict[int, Migration] = {}
    package_files = resources.files(package)
    for entry in sorted(package_files.iterdir(), key=lambda item: item.name):
        if not entry.is_file():
            continue
        match = MIGRATION_PATTERN.match(entry.name)
        if match is None:
            continue
        version = int(match.group(1))
        if version in migrations_by_version:
            raise MigrationError(
                f"duplicate migration version {version:04d}: "
                f"{migrations_by_version[version].filename} and {entry.name}"
            )
        sql = entry.read_text(encoding="utf-8")
        migrations_by_version[version] = Migration(
            version=version,
            filename=entry.name,
            sql=sql,
        )
    return [migrations_by_version[version] for version in sorted(migrations_by_version)]


def discover_migrations_from_paths(paths: Iterable[Path]) -> list[Migration]:
    """Discover migrations from explicit filesystem paths for tests."""
    migrations_by_version: dict[int, Migration] = {}
    for path in sorted(paths, key=lambda item: item.name):
        match = MIGRATION_PATTERN.match(path.name)
        if match is None:
            continue
        version = int(match.group(1))
        if version in migrations_by_version:
            raise MigrationError(
                f"duplicate migration version {version:04d}: "
                f"{migrations_by_version[version].filename} and {path.name}"
            )
        sql = path.read_text(encoding="utf-8")
        migrations_by_version[version] = Migration(
            version=version,
            filename=path.name,
            sql=sql,
        )
    return [migrations_by_version[version] for version in sorted(migrations_by_version)]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _split_sql_statements(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def _execute_sql_script(connection: sqlite3.Connection, sql: str) -> None:
    for statement in _split_sql_statements(sql):
        connection.execute(statement)


def _load_applied_migrations(connection: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    table_exists = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
    ).fetchone()
    if table_exists is None:
        return {}
    rows = connection.execute(
        "SELECT version, filename, checksum FROM schema_migrations ORDER BY version"
    ).fetchall()
    return {int(row["version"]): (row["filename"], row["checksum"]) for row in rows}


def apply_migrations(
    database: str | Path,
    *,
    migrations: list[Migration] | None = None,
) -> None:
    """Apply packaged migrations transactionally; no-op when already current."""
    migration_list = discover_migrations() if migrations is None else migrations
    connection = connect_sqlite(database)
    try:
        applied = _load_applied_migrations(connection)
        for migration in migration_list:
            if migration.version in applied:
                recorded_filename, recorded_checksum = applied[migration.version]
                if recorded_filename != migration.filename:
                    raise MigrationError(
                        f"migration version {migration.version:04d} filename mismatch: "
                        f"applied {recorded_filename!r}, found {migration.filename!r}"
                    )
                if recorded_checksum != migration.checksum:
                    raise MigrationError(
                        f"migration version {migration.version:04d} checksum mismatch for "
                        f"{migration.filename}"
                    )
                continue
            try:
                connection.execute("BEGIN")
                _execute_sql_script(connection, migration.sql)
                connection.execute(
                    """
                    INSERT INTO schema_migrations (version, filename, checksum, applied_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        migration.version,
                        migration.filename,
                        migration.checksum,
                        _utc_now_iso(),
                    ),
                )
                connection.commit()
                applied[migration.version] = (migration.filename, migration.checksum)
            except Exception:
                connection.rollback()
                raise
    finally:
        connection.close()
