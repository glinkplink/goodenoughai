from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from goodenough_bench.boundaries import BatchStatus, BenchmarkBatch
from goodenough_bench.db import connect_sqlite
from goodenough_bench.exceptions import MigrationError
from goodenough_bench.migrations.runner import (
    Migration,
    apply_migrations,
    discover_migrations,
    discover_migrations_from_paths,
)
from pydantic import ValidationError


CHECKSUM = "a" * 64
DATASET_COMMIT = "b" * 40
RUNNER_COMMIT = "c" * 40
STARTED = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


def planned_batch() -> BenchmarkBatch:
    return BenchmarkBatch(
        batch_id="batch-001",
        dataset_version="automation-mvp-v0.1.0",
        dataset_commit=DATASET_COMMIT,
        runner_commit=RUNNER_COMMIT,
        prompt_version="automation-prompt-v0.1.0",
        run_order_seed=42,
        operator="operator-1",
        environment="TheImp",
        status=BatchStatus.PLANNED,
        started_at=None,
        completed_at=None,
        invalid_run_count=0,
        valid_for_scoring_count=0,
    )


class BenchmarkBatchBoundaryTests(unittest.TestCase):
    def test_valid_planned_running_completed_and_frozen_batches(self) -> None:
        planned = planned_batch()
        self.assertIsNone(planned.started_at)
        self.assertIsNone(planned.completed_at)

        running = planned.model_copy(
            update={
                "status": BatchStatus.RUNNING,
                "started_at": STARTED,
                "completed_at": None,
            }
        )
        self.assertEqual(running.status, BatchStatus.RUNNING)

        completed = planned.model_copy(
            update={
                "status": BatchStatus.COMPLETED,
                "started_at": STARTED,
                "completed_at": STARTED + timedelta(hours=1),
                "valid_for_scoring_count": 10,
            }
        )
        self.assertEqual(completed.valid_for_scoring_count, 10)

        frozen = completed.model_copy(update={"status": BatchStatus.FROZEN})
        self.assertEqual(frozen.status, BatchStatus.FROZEN)

    def test_status_timestamp_validation_rules(self) -> None:
        with self.assertRaisesRegex(ValidationError, "planned batches require"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump() | {"started_at": STARTED.isoformat()}
            )

        with self.assertRaisesRegex(ValidationError, "running batches require"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump()
                | {
                    "status": BatchStatus.RUNNING.value,
                    "started_at": None,
                }
            )

        with self.assertRaisesRegex(ValidationError, "completed or frozen batches require"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump()
                | {
                    "status": BatchStatus.COMPLETED.value,
                    "started_at": STARTED.isoformat(),
                    "completed_at": None,
                }
            )

        with self.assertRaisesRegex(ValidationError, "completed_at cannot precede"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump()
                | {
                    "status": BatchStatus.COMPLETED.value,
                    "started_at": STARTED.isoformat(),
                    "completed_at": (STARTED - timedelta(minutes=1)).isoformat(),
                }
            )

    def test_timestamps_must_be_utc(self) -> None:
        local_started = datetime(2026, 7, 31, 12, 0)
        with self.assertRaisesRegex(ValidationError, "must include a UTC offset"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump()
                | {
                    "status": BatchStatus.RUNNING.value,
                    "started_at": local_started.isoformat(),
                }
            )

    def test_batch_json_schema_generates(self) -> None:
        schema = BenchmarkBatch.model_json_schema()
        self.assertEqual(schema["title"], "BenchmarkBatch")
        self.assertIn("batch_id", schema["properties"])


class MigrationRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.database = Path(self._tmpdir.name) / "test.db"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_clean_database_creation_from_migrations(self) -> None:
        apply_migrations(self.database)
        connection = connect_sqlite(self.database)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            self.assertEqual(
                tables,
                {"schema_migrations", "benchmark_batches", "planned_runs"},
            )
            migration_row = connection.execute(
                "SELECT version, filename, checksum, applied_at FROM schema_migrations"
            ).fetchone()
            self.assertIsNotNone(migration_row)
            assert migration_row is not None
            self.assertEqual(migration_row["version"], 1)
            self.assertEqual(migration_row["filename"], "0001_initial.sql")
            self.assertEqual(len(migration_row["checksum"]), 64)
            self.assertTrue(migration_row["applied_at"].endswith("+00:00"))
        finally:
            connection.close()

    def test_migration_reapplication_is_no_op(self) -> None:
        apply_migrations(self.database)
        connection = connect_sqlite(self.database)
        try:
            first_count = connection.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0]
        finally:
            connection.close()

        apply_migrations(self.database)

        connection = connect_sqlite(self.database)
        try:
            second_count = connection.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0]
            self.assertEqual(first_count, second_count)
        finally:
            connection.close()

    def test_discover_migrations_in_deterministic_version_order(self) -> None:
        migrations = discover_migrations()
        versions = [migration.version for migration in migrations]
        self.assertEqual(versions, sorted(versions))
        self.assertGreaterEqual(len(migrations), 1)
        self.assertEqual(migrations[0].filename, "0001_initial.sql")

    def test_duplicate_migration_version_rejection(self) -> None:
        directory = Path(self._tmpdir.name) / "dupes"
        directory.mkdir()
        (directory / "0002_first.sql").write_text("SELECT 1;", encoding="utf-8")
        (directory / "0002_second.sql").write_text("SELECT 2;", encoding="utf-8")
        with self.assertRaisesRegex(MigrationError, "duplicate migration version"):
            discover_migrations_from_paths(directory.iterdir())

    def test_applied_migration_checksum_mismatch_rejection(self) -> None:
        apply_migrations(self.database)
        packaged = discover_migrations()[0]
        tampered = Migration(
            version=packaged.version,
            filename=packaged.filename,
            sql=packaged.sql + "\n-- changed",
        )
        with self.assertRaisesRegex(MigrationError, "checksum mismatch"):
            apply_migrations(self.database, migrations=[tampered])

    def test_failing_migration_rolls_back_without_recording(self) -> None:
        good = discover_migrations()[0]
        failing = Migration(
            version=2,
            filename="0002_failing.sql",
            sql="CREATE TABLE migration_probe (id INTEGER PRIMARY KEY); INVALID SQL HERE;",
        )
        with self.assertRaises(sqlite3.OperationalError):
            apply_migrations(self.database, migrations=[good, failing])

        connection = connect_sqlite(self.database)
        try:
            versions = [
                row["version"]
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                ).fetchall()
            ]
            self.assertEqual(versions, [1])
            probe_exists = connection.execute(
                "SELECT name FROM sqlite_master WHERE name = 'migration_probe'"
            ).fetchone()
            self.assertIsNone(probe_exists)
        finally:
            connection.close()

    def test_foreign_key_enforcement(self) -> None:
        apply_migrations(self.database)
        connection = connect_sqlite(self.database)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO planned_runs (
                        run_id,
                        batch_id,
                        case_id,
                        case_version,
                        model_profile_id,
                        rep_index,
                        run_order_seed,
                        dataset_version,
                        dataset_commit,
                        runner_commit,
                        prompt_version,
                        prompt_hash,
                        exact_model_identifier,
                        displayed_model_name,
                        provider,
                        provider_surface,
                        provider_host,
                        collection_method,
                        model_identity_confidence,
                        source_type,
                        execution_environment,
                        runtime,
                        quantization,
                        hardware_profile_id,
                        pricing_snapshot_id,
                        model_parameters_json
                    ) VALUES (
                        'run-orphan',
                        'missing-batch',
                        'case-001',
                        '0.1.0',
                        'profile-001',
                        0,
                        42,
                        'automation-mvp-v0.1.0',
                        ?,
                        ?,
                        'automation-prompt-v0.1.0',
                        ?,
                        'qwen3.5:9b',
                        'Qwen 3.5 9B',
                        'ollama',
                        'ollama_local',
                        'localhost',
                        'goodenough-ollama-adapter/0.1.0',
                        'high',
                        'local_exact',
                        'local',
                        'ollama 0.32.5',
                        'Q4_K_M',
                        'theimp-2026-07-31-ollama-0.32.5',
                        NULL,
                        '{"frequency_penalty":null,"max_output_tokens":256,"presence_penalty":null,"reasoning_mode":null,"response_format":"json_schema","seed":null,"temperature":0.0,"top_p":null}'
                    )
                    """,
                    (DATASET_COMMIT, RUNNER_COMMIT, CHECKSUM),
                )
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
