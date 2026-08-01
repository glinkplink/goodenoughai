from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from goodenough_bench.boundaries import BatchPurpose, BatchStatus, BenchmarkBatch
from goodenough_bench.db import connect_sqlite
from goodenough_bench.exceptions import MigrationError
from goodenough_bench.migrations.runner import (
    Migration,
    apply_migrations,
    discover_migrations,
    discover_migrations_from_paths,
)
from goodenough_bench.repository import SQLiteRepository
from pydantic import ValidationError


CHECKSUM = "a" * 64
DATASET_COMMIT = "b" * 40
RUNNER_COMMIT = "c" * 40
STARTED = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


def planned_batch() -> BenchmarkBatch:
    return BenchmarkBatch(
        batch_id="batch-001",
        batch_purpose=BatchPurpose.DIAGNOSTIC_PILOT,
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


class BatchPurposeBoundaryTests(unittest.TestCase):
    def test_batch_purpose_enum_values(self) -> None:
        self.assertEqual(BatchPurpose.DIAGNOSTIC_PILOT.value, "diagnostic_pilot")
        self.assertEqual(BatchPurpose.STABLE_BENCHMARK.value, "stable_benchmark")
        self.assertEqual(len(BatchPurpose), 2)

    def test_batch_purpose_required_on_benchmark_batch(self) -> None:
        with self.assertRaises(ValidationError):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump(exclude={"batch_purpose"})
            )

    def test_batch_purpose_in_json_schema(self) -> None:
        schema = BenchmarkBatch.model_json_schema()
        self.assertIn("batch_purpose", schema["properties"])


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

        frozen = completed.model_copy(
            update={
                "status": BatchStatus.FROZEN,
                "reproduction_checksum": CHECKSUM,
            }
        )
        self.assertEqual(frozen.status, BatchStatus.FROZEN)
        self.assertEqual(frozen.reproduction_checksum, CHECKSUM)

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
            migration_rows = connection.execute(
                "SELECT version, filename, checksum, applied_at FROM schema_migrations ORDER BY version"
            ).fetchall()
            self.assertEqual(len(migration_rows), 4)
            self.assertEqual(migration_rows[0]["version"], 1)
            self.assertEqual(migration_rows[0]["filename"], "0001_initial.sql")
            self.assertEqual(migration_rows[1]["version"], 2)
            self.assertEqual(migration_rows[1]["filename"], "0002_batch_purpose.sql")
            self.assertEqual(migration_rows[2]["version"], 3)
            self.assertEqual(
                migration_rows[2]["filename"],
                "0003_model_route_provenance.sql",
            )
            self.assertEqual(migration_rows[3]["version"], 4)
            self.assertEqual(
                migration_rows[3]["filename"],
                "0004_reproduction_checksum.sql",
            )
            for row in migration_rows:
                self.assertEqual(len(row["checksum"]), 64)
                self.assertTrue(row["applied_at"].endswith("+00:00"))
            batch_columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(benchmark_batches)"
                ).fetchall()
            }
            self.assertIn("batch_purpose", batch_columns)
            self.assertIn("reproduction_checksum", batch_columns)
            planned_run_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(planned_runs)").fetchall()
            }
            self.assertIn("local_model_identity_json", planned_run_columns)
            self.assertIn("routed_provider_identity_json", planned_run_columns)
            self.assertIn("profile_provenance_complete", planned_run_columns)
        finally:
            connection.close()

    def test_upgrade_from_populated_0001_database_labels_diagnostic_pilot(self) -> None:
        initial_only = discover_migrations()[0]
        apply_migrations(self.database, migrations=[initial_only])
        connection = connect_sqlite(self.database)
        try:
            connection.execute(
                """
                INSERT INTO benchmark_batches (
                    batch_id,
                    dataset_version,
                    dataset_commit,
                    runner_commit,
                    prompt_version,
                    run_order_seed,
                    operator,
                    environment,
                    status,
                    started_at,
                    completed_at,
                    invalid_run_count,
                    valid_for_scoring_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "batch-legacy",
                    "automation-mvp-v0.1.0",
                    DATASET_COMMIT,
                    RUNNER_COMMIT,
                    "automation-prompt-v0.1.0",
                    42,
                    "operator-1",
                    "TheImp",
                    BatchStatus.PLANNED.value,
                    None,
                    None,
                    0,
                    0,
                ),
            )
            connection.executemany(
                """
                INSERT INTO planned_runs (
                    run_id, batch_id, case_id, case_version, model_profile_id,
                    rep_index, run_order_seed, dataset_version, dataset_commit,
                    runner_commit, prompt_version, prompt_hash,
                    exact_model_identifier, displayed_model_name, provider,
                    provider_surface, provider_host, collection_method,
                    model_identity_confidence, source_type, execution_environment,
                    runtime, quantization, hardware_profile_id, pricing_snapshot_id,
                    model_parameters_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        "run-legacy",
                        "batch-legacy",
                        "case-legacy",
                        "0.1.0",
                        "profile-legacy",
                        0,
                        42,
                        "automation-mvp-v0.1.0",
                        DATASET_COMMIT,
                        RUNNER_COMMIT,
                        "automation-prompt-v0.1.0",
                        CHECKSUM,
                        "opaque-import",
                        "Legacy manual import",
                        "manual",
                        "manual_import",
                        None,
                        "legacy-import/0.1.0",
                        "high",
                        "manual_import",
                        "import",
                        None,
                        None,
                        None,
                        None,
                        '{"frequency_penalty":null,"max_output_tokens":256,"presence_penalty":null,"reasoning_mode":null,"response_format":"json_schema","seed":null,"temperature":0.0,"top_p":null}',
                    ),
                    (
                        "run-legacy-local",
                        "batch-legacy",
                        "case-legacy-local",
                        "0.1.0",
                        "profile-legacy-local",
                        0,
                        42,
                        "automation-mvp-v0.1.0",
                        DATASET_COMMIT,
                        RUNNER_COMMIT,
                        "automation-prompt-v0.1.0",
                        CHECKSUM,
                        "qwen3.5:9b",
                        "Legacy Qwen",
                        "ollama",
                        "ollama_local",
                        "localhost",
                        "legacy-adapter/0.1.0",
                        "high",
                        "local_exact",
                        "local",
                        "ollama 0.32.5",
                        "Q4_K_M",
                        "theimp-legacy",
                        None,
                        '{"frequency_penalty":null,"max_output_tokens":256,"presence_penalty":null,"reasoning_mode":null,"response_format":"json_schema","seed":null,"temperature":0.0,"top_p":null}',
                    ),
                ),
            )
            connection.commit()
        finally:
            connection.close()

        apply_migrations(self.database)

        connection = connect_sqlite(self.database)
        try:
            row = connection.execute(
                "SELECT batch_purpose FROM benchmark_batches WHERE batch_id = ?",
                ("batch-legacy",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["batch_purpose"], BatchPurpose.DIAGNOSTIC_PILOT.value)
            legacy_row = connection.execute(
                """
                SELECT local_model_identity_json, routed_provider_identity_json,
                       profile_provenance_complete
                FROM planned_runs WHERE run_id = ?
                """,
                ("run-legacy",),
            ).fetchone()
            self.assertIsNotNone(legacy_row)
            assert legacy_row is not None
            self.assertIsNone(legacy_row["local_model_identity_json"])
            self.assertIsNone(legacy_row["routed_provider_identity_json"])
            self.assertEqual(legacy_row["profile_provenance_complete"], 0)

            repository = SQLiteRepository(connection)
            legacy = repository.get_planned_run("run-legacy")
            self.assertIsNotNone(legacy)
            assert legacy is not None
            self.assertFalse(legacy.profile_provenance_complete)
            self.assertIsNone(legacy.local_model_identity)
            self.assertEqual(legacy.source_type.value, "manual_import")
            self.assertEqual(legacy.model_identity_confidence.value, "high")

            legacy_local = repository.get_planned_run("run-legacy-local")
            self.assertIsNotNone(legacy_local)
            assert legacy_local is not None
            self.assertFalse(legacy_local.profile_provenance_complete)
            self.assertIsNone(legacy_local.local_model_identity)
        finally:
            connection.close()

    def test_upgrade_reclassifies_legacy_frozen_batch_until_refrozen(self) -> None:
        initial_only, batch_purpose, route_provenance = discover_migrations()[:3]
        apply_migrations(
            self.database,
            migrations=[initial_only, batch_purpose, route_provenance],
        )
        connection = connect_sqlite(self.database)
        try:
            connection.execute(
                """
                INSERT INTO benchmark_batches (
                    batch_id,
                    dataset_version,
                    dataset_commit,
                    runner_commit,
                    prompt_version,
                    run_order_seed,
                    operator,
                    environment,
                    status,
                    started_at,
                    completed_at,
                    invalid_run_count,
                    valid_for_scoring_count,
                    batch_purpose
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "batch-legacy-frozen",
                    "automation-mvp-v0.1.0",
                    DATASET_COMMIT,
                    RUNNER_COMMIT,
                    "automation-prompt-v0.1.0",
                    42,
                    "operator-1",
                    "TheImp",
                    BatchStatus.FROZEN.value,
                    STARTED.isoformat(),
                    (STARTED + timedelta(hours=1)).isoformat(),
                    0,
                    3,
                    BatchPurpose.DIAGNOSTIC_PILOT.value,
                ),
            )
            connection.commit()
        finally:
            connection.close()

        apply_migrations(self.database)

        connection = connect_sqlite(self.database)
        try:
            row = connection.execute(
                """
                SELECT status, reproduction_checksum
                FROM benchmark_batches
                WHERE batch_id = ?
                """,
                ("batch-legacy-frozen",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["status"], BatchStatus.COMPLETED.value)
            self.assertIsNone(row["reproduction_checksum"])
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

    def test_migration_with_semicolon_inside_string_literal(self) -> None:
        good = discover_migrations()[0]
        literal_migration = Migration(
            version=2,
            filename="0002_literal.sql",
            sql=(
                "CREATE TABLE literal_probe (value TEXT NOT NULL); "
                "INSERT INTO literal_probe (value) VALUES ('a;b');"
            ),
        )
        apply_migrations(self.database, migrations=[good, literal_migration])
        connection = connect_sqlite(self.database)
        try:
            row = connection.execute(
                "SELECT value FROM literal_probe"
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["value"], "a;b")
        finally:
            connection.close()

    def test_migration_allows_trailing_sql_comment(self) -> None:
        good = discover_migrations()[0]
        comment_migration = Migration(
            version=2,
            filename="0002_comment.sql",
            sql="CREATE TABLE comment_probe (id INTEGER PRIMARY KEY);\n-- trailing comment",
        )
        apply_migrations(self.database, migrations=[good, comment_migration])
        connection = connect_sqlite(self.database)
        try:
            probe_exists = connection.execute(
                "SELECT name FROM sqlite_master WHERE name = 'comment_probe'"
            ).fetchone()
            self.assertIsNotNone(probe_exists)
        finally:
            connection.close()

    def test_migration_with_trigger_containing_internal_semicolons(self) -> None:
        good = discover_migrations()[0]
        trigger_migration = Migration(
            version=2,
            filename="0002_trigger.sql",
            sql="""
CREATE TABLE trigger_source (id INTEGER PRIMARY KEY, value INTEGER NOT NULL);
CREATE TABLE trigger_log (id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL);
CREATE TRIGGER trigger_source_after_insert
AFTER INSERT ON trigger_source
BEGIN
    INSERT INTO trigger_log (source_id) VALUES (NEW.id);
    UPDATE trigger_source SET value = value + 1 WHERE id = NEW.id;
END;
""",
        )
        apply_migrations(self.database, migrations=[good, trigger_migration])
        connection = connect_sqlite(self.database)
        try:
            connection.execute("INSERT INTO trigger_source (value) VALUES (1)")
            connection.commit()
            log_count = connection.execute(
                "SELECT COUNT(*) FROM trigger_log"
            ).fetchone()[0]
            updated_value = connection.execute(
                "SELECT value FROM trigger_source WHERE id = 1"
            ).fetchone()[0]
            self.assertEqual(log_count, 1)
            self.assertEqual(updated_value, 2)
        finally:
            connection.close()

    def test_incomplete_trailing_migration_sql_rejected(self) -> None:
        good = discover_migrations()[0]
        incomplete = Migration(
            version=2,
            filename="0002_incomplete.sql",
            sql="CREATE TABLE incomplete_probe (id INTEGER PRIMARY KEY",
        )
        with self.assertRaisesRegex(MigrationError, "incomplete trailing SQL statement"):
            apply_migrations(self.database, migrations=[good, incomplete])

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
                "SELECT name FROM sqlite_master WHERE name = 'incomplete_probe'"
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
