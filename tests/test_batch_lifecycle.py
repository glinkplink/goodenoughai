from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from goodenough_bench.boundaries import (
    BatchPurpose,
    BatchStatus,
    BenchmarkBatch,
    ExecutionEnvironment,
    IdentityConfidence,
    LocalModelIdentity,
    ModelParameters,
    ModelProfileReference,
    PlannedRun,
    ProviderSurface,
    SourceType,
)
from goodenough_bench.cli import main
from goodenough_bench.exceptions import BatchLifecycleError, RepositoryConflictError
from goodenough_bench.profile_loaders import load_model_profiles, load_pricing_snapshots
from goodenough_bench.reproduction import (
    BatchReproductionReport,
    compute_reproduction_checksum,
    verify_batch_reproduction,
)
from goodenough_bench.repository import SQLiteRepository


CHECKSUM = "a" * 64
DATASET_COMMIT = "b" * 40
RUNNER_COMMIT = "c" * 40
STARTED = datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc)
COMPLETED = datetime(2026, 8, 1, 15, 0, tzinfo=timezone.utc)


def model_parameters() -> ModelParameters:
    return ModelParameters(
        temperature=0.0,
        max_output_tokens=256,
        reasoning_mode=None,
        response_format="json_schema",
        seed=None,
        top_p=None,
        frequency_penalty=None,
        presence_penalty=None,
    )


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
        reproduction_checksum=None,
    )


def planned_run(*, run_id: str = "run-001", rep_index: int = 0) -> PlannedRun:
    return PlannedRun(
        run_id=run_id,
        batch_id="batch-001",
        case_id="extraction_invoice_001",
        case_version="0.1.0",
        model_profile_id="qwen35-9b-ollama-q4km",
        rep_index=rep_index,
        run_order_seed=42,
        dataset_version="automation-mvp-v0.1.0",
        dataset_commit=DATASET_COMMIT,
        runner_commit=RUNNER_COMMIT,
        prompt_version="automation-prompt-v0.1.0",
        prompt_hash=CHECKSUM,
        exact_model_identifier="qwen3.5:9b",
        displayed_model_name="Qwen 3.5 9B",
        provider="ollama",
        provider_surface=ProviderSurface.OLLAMA_LOCAL,
        provider_host="localhost",
        collection_method="goodenough-ollama-adapter/0.1.0",
        model_identity_confidence=IdentityConfidence.HIGH,
        source_type=SourceType.LOCAL_EXACT,
        execution_environment=ExecutionEnvironment.LOCAL,
        runtime="ollama 0.32.5",
        quantization="Q4_K_M",
        hardware_profile_id="theimp-2026-07-31-ollama-0.32.5",
        local_model_identity=LocalModelIdentity(
            artifact_digest="1" * 64,
            artifact_size_bytes=6_594_474_711,
            parameter_size="9.7B",
            context_window_tokens=4096,
        ),
        routed_provider_identity=None,
        profile_provenance_complete=True,
        pricing_snapshot_id=None,
        model_parameters=model_parameters(),
    )


def routed_planned_run(*, run_id: str = "run-routed-001") -> PlannedRun:
    profile = load_model_profiles().profile_by_id()["synthetic-openrouter-deepseek-v4-flash-api"]
    return PlannedRun.model_validate(
        {
            **planned_run(run_id=run_id).model_dump(mode="python"),
            **profile.model_dump(
                mode="python",
                include=set(ModelProfileReference.model_fields),
            ),
        }
    )


class BatchLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.database = Path(self._tmpdir.name) / "test.db"
        self.repository = SQLiteRepository.from_database(self.database)
        self.pricing_catalog = load_pricing_snapshots()

    def tearDown(self) -> None:
        self.repository.close()
        self._tmpdir.cleanup()

    def _seed_planned_batch_with_run(self) -> None:
        self.repository.create_batch(planned_batch())
        self.repository.create_planned_run(planned_run())

    def _freeze_batch(self) -> BenchmarkBatch:
        self.repository.transition_batch("batch-001", BatchStatus.RUNNING, at=STARTED)
        self.repository.transition_batch(
            "batch-001", BatchStatus.COMPLETED, at=COMPLETED
        )
        return self.repository.transition_batch("batch-001", BatchStatus.FROZEN)

    def test_planned_to_running_to_completed_to_frozen(self) -> None:
        self._seed_planned_batch_with_run()

        running = self.repository.transition_batch(
            "batch-001", BatchStatus.RUNNING, at=STARTED
        )
        self.assertEqual(running.status, BatchStatus.RUNNING)
        self.assertEqual(running.started_at, STARTED)
        self.assertIsNone(running.completed_at)
        self.assertIsNone(running.reproduction_checksum)

        completed = self.repository.transition_batch(
            "batch-001",
            BatchStatus.COMPLETED,
            at=COMPLETED,
            invalid_run_count=1,
            valid_for_scoring_count=2,
        )
        self.assertEqual(completed.status, BatchStatus.COMPLETED)
        self.assertEqual(completed.started_at, STARTED)
        self.assertEqual(completed.completed_at, COMPLETED)
        self.assertEqual(completed.invalid_run_count, 1)
        self.assertEqual(completed.valid_for_scoring_count, 2)
        self.assertIsNone(completed.reproduction_checksum)

        frozen = self.repository.transition_batch("batch-001", BatchStatus.FROZEN)
        self.assertEqual(frozen.status, BatchStatus.FROZEN)
        self.assertIsNotNone(frozen.reproduction_checksum)
        expected = compute_reproduction_checksum(
            frozen, self.repository.list_planned_runs_for_batch("batch-001")
        )
        self.assertEqual(frozen.reproduction_checksum, expected)

        fetched = self.repository.get_batch("batch-001")
        assert fetched is not None
        self.assertEqual(fetched.status, BatchStatus.FROZEN)
        self.assertEqual(fetched.reproduction_checksum, expected)

    def test_illegal_transition_rejected(self) -> None:
        self.repository.create_batch(planned_batch())
        with self.assertRaises(BatchLifecycleError):
            self.repository.transition_batch(
                "batch-001", BatchStatus.COMPLETED, at=COMPLETED
            )
        with self.assertRaises(BatchLifecycleError):
            self.repository.transition_batch(
                "batch-001", BatchStatus.FROZEN
            )

    def test_new_batch_must_start_planned(self) -> None:
        running = planned_batch().model_copy(
            update={"status": BatchStatus.RUNNING, "started_at": STARTED}
        )
        with self.assertRaisesRegex(BatchLifecycleError, "created with status 'planned'"):
            self.repository.create_batch(running)

    def test_backward_and_skip_transitions_rejected(self) -> None:
        self._seed_planned_batch_with_run()
        self.repository.transition_batch("batch-001", BatchStatus.RUNNING, at=STARTED)
        with self.assertRaises(BatchLifecycleError):
            self.repository.transition_batch("batch-001", BatchStatus.PLANNED)
        self.repository.transition_batch(
            "batch-001", BatchStatus.COMPLETED, at=COMPLETED
        )
        with self.assertRaises(BatchLifecycleError):
            self.repository.transition_batch(
                "batch-001", BatchStatus.RUNNING, at=STARTED
            )

    def test_freeze_requires_at_least_one_planned_run(self) -> None:
        self.repository.create_batch(planned_batch())
        self.repository.transition_batch("batch-001", BatchStatus.RUNNING, at=STARTED)
        self.repository.transition_batch(
            "batch-001", BatchStatus.COMPLETED, at=COMPLETED
        )
        with self.assertRaisesRegex(BatchLifecycleError, "planned run"):
            self.repository.transition_batch("batch-001", BatchStatus.FROZEN)

    def test_freeze_rejects_legacy_incomplete_planned_runs(self) -> None:
        self.repository.create_batch(planned_batch())
        self.repository._connection.execute(
            """
            INSERT INTO planned_runs (
                run_id, batch_id, case_id, case_version, model_profile_id,
                rep_index, run_order_seed, dataset_version, dataset_commit,
                runner_commit, prompt_version, prompt_hash,
                exact_model_identifier, displayed_model_name, provider,
                provider_surface, provider_host, collection_method,
                model_identity_confidence, source_type, execution_environment,
                runtime, quantization, hardware_profile_id,
                local_model_identity_json, routed_provider_identity_json,
                profile_provenance_complete, pricing_snapshot_id,
                model_parameters_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "run-legacy",
                "batch-001",
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
                None,
                0,
                None,
                '{"frequency_penalty":null,"max_output_tokens":256,"presence_penalty":null,"reasoning_mode":null,"response_format":"json_schema","seed":null,"temperature":0.0,"top_p":null}',
            ),
        )
        self.repository._connection.commit()
        self.repository.transition_batch("batch-001", BatchStatus.RUNNING, at=STARTED)
        self.repository.transition_batch(
            "batch-001", BatchStatus.COMPLETED, at=COMPLETED
        )
        with self.assertRaisesRegex(
            BatchLifecycleError, "incomplete planned-run provenance"
        ):
            self.repository.transition_batch("batch-001", BatchStatus.FROZEN)

    def test_planned_runs_rejected_after_batch_leaves_planned(self) -> None:
        self.repository.create_batch(planned_batch())
        self.repository.transition_batch("batch-001", BatchStatus.RUNNING, at=STARTED)
        with self.assertRaises(RepositoryConflictError):
            self.repository.create_planned_run(planned_run())

    def test_planned_run_insert_rechecks_parent_status_atomically(self) -> None:
        self.repository.create_batch(planned_batch())
        competing_repository = SQLiteRepository.from_database(self.database)
        original_get_planned_run = self.repository.get_planned_run

        def transition_before_insert(run_id: str) -> PlannedRun | None:
            competing_repository.transition_batch(
                "batch-001", BatchStatus.RUNNING, at=STARTED
            )
            return original_get_planned_run(run_id)

        try:
            with mock.patch.object(
                self.repository,
                "get_planned_run",
                side_effect=transition_before_insert,
            ):
                with self.assertRaisesRegex(RepositoryConflictError, "planned"):
                    self.repository.create_planned_run(planned_run())
        finally:
            competing_repository.close()

        self.assertEqual(self.repository.list_planned_runs_for_batch("batch-001"), [])

    def test_stale_transition_cannot_overwrite_newer_state(self) -> None:
        self._seed_planned_batch_with_run()
        competing_repository = SQLiteRepository.from_database(self.database)
        original_list_planned_runs = self.repository.list_planned_runs_for_batch

        def advance_to_frozen(batch_id: str) -> list[PlannedRun]:
            competing_repository.transition_batch(
                batch_id, BatchStatus.RUNNING, at=STARTED
            )
            competing_repository.transition_batch(
                batch_id, BatchStatus.COMPLETED, at=COMPLETED
            )
            competing_repository.transition_batch(batch_id, BatchStatus.FROZEN)
            return original_list_planned_runs(batch_id)

        try:
            with mock.patch.object(
                self.repository,
                "list_planned_runs_for_batch",
                side_effect=advance_to_frozen,
            ):
                with self.assertRaisesRegex(BatchLifecycleError, "changed concurrently"):
                    self.repository.transition_batch(
                        "batch-001", BatchStatus.RUNNING, at=STARTED
                    )
        finally:
            competing_repository.close()

        stored = self.repository.get_batch("batch-001")
        assert stored is not None
        self.assertEqual(stored.status, BatchStatus.FROZEN)
        self.assertEqual(stored.completed_at, COMPLETED)
        self.assertIsNotNone(stored.reproduction_checksum)

    def test_start_rejects_run_count_updates(self) -> None:
        self._seed_planned_batch_with_run()
        with self.assertRaisesRegex(BatchLifecycleError, "run-count updates"):
            self.repository.transition_batch(
                "batch-001",
                BatchStatus.RUNNING,
                at=STARTED,
                invalid_run_count=1,
            )

    def test_transition_rejects_non_enum_status(self) -> None:
        self._seed_planned_batch_with_run()
        with self.assertRaisesRegex(BatchLifecycleError, "must be a BatchStatus"):
            self.repository.transition_batch(  # type: ignore[arg-type]
                "batch-001", "running", at=STARTED
            )

    def test_frozen_batch_rejects_further_transitions(self) -> None:
        self._seed_planned_batch_with_run()
        self._freeze_batch()
        with self.assertRaises(BatchLifecycleError):
            self.repository.transition_batch(
                "batch-001", BatchStatus.COMPLETED, at=COMPLETED
            )

    def test_reproduction_checksum_is_deterministic_and_sensitive(self) -> None:
        batch = planned_batch()
        runs = [planned_run(), planned_run(run_id="run-002", rep_index=1)]
        first = compute_reproduction_checksum(batch, runs)
        second = compute_reproduction_checksum(batch, list(reversed(runs)))
        self.assertEqual(first, second)
        altered = planned_run().model_copy(
            update={"exact_model_identifier": "qwen3.5:9b-altered"}
        )
        self.assertNotEqual(
            first, compute_reproduction_checksum(batch, [altered, runs[1]])
        )
        self.assertNotEqual(
            first,
            compute_reproduction_checksum(
                batch.model_copy(update={"operator": "operator-2"}), runs
            ),
        )
        updated_parameters = model_parameters().model_copy(update={"temperature": 0.1})
        self.assertNotEqual(
            first,
            compute_reproduction_checksum(
                batch,
                [runs[0].model_copy(update={"model_parameters": updated_parameters}), runs[1]],
            ),
        )
        assert runs[0].local_model_identity is not None
        tampered_local = runs[0].local_model_identity.model_copy(
            update={"artifact_digest": "9" * 64}
        )
        self.assertNotEqual(
            first,
            compute_reproduction_checksum(
                batch,
                [runs[0].model_copy(update={"local_model_identity": tampered_local}), runs[1]],
            ),
        )

    def test_verify_reproduction_ok_for_frozen_batch(self) -> None:
        self._seed_planned_batch_with_run()
        frozen = self._freeze_batch()
        report = verify_batch_reproduction(self.repository, "batch-001")
        self.assertIsInstance(report, BatchReproductionReport)
        self.assertTrue(report.verified)
        self.assertEqual(report.status, "ok")
        self.assertEqual(report.stored_checksum, frozen.reproduction_checksum)
        self.assertEqual(report.computed_checksum, frozen.reproduction_checksum)

    def test_verify_reproduction_detects_planned_run_tamper(self) -> None:
        self._seed_planned_batch_with_run()
        frozen = self._freeze_batch()
        assert frozen.reproduction_checksum is not None

        self.repository._connection.execute(
            "UPDATE planned_runs SET exact_model_identifier = ? WHERE run_id = ?",
            ("tampered-model", "run-001"),
        )
        self.repository._connection.commit()

        report = verify_batch_reproduction(self.repository, "batch-001")
        self.assertFalse(report.verified)
        self.assertEqual(report.status, "mismatch")
        self.assertEqual(report.stored_checksum, frozen.reproduction_checksum)
        self.assertNotEqual(report.computed_checksum, report.stored_checksum)

    def test_verify_reproduction_detects_routed_provider_identity_tamper(self) -> None:
        self.repository.create_batch(planned_batch())
        routed = routed_planned_run()
        self.repository.create_planned_run(
            routed,
            pricing_catalog=self.pricing_catalog,
        )
        frozen = self._freeze_batch()
        assert frozen.reproduction_checksum is not None
        assert routed.routed_provider_identity is not None

        tampered_identity = routed.routed_provider_identity.model_copy(
            update={"upstream_model_identifier": "deepseek-tampered"}
        )
        self.repository._connection.execute(
            "UPDATE planned_runs SET routed_provider_identity_json = ? WHERE run_id = ?",
            (
                json.dumps(
                    tampered_identity.model_dump(mode="json"),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                routed.run_id,
            ),
        )
        self.repository._connection.commit()

        report = verify_batch_reproduction(self.repository, "batch-001")
        self.assertFalse(report.verified)
        self.assertEqual(report.status, "mismatch")
        self.assertEqual(report.stored_checksum, frozen.reproduction_checksum)
        self.assertNotEqual(report.computed_checksum, report.stored_checksum)

    def test_verify_reproduction_reports_invalid_persisted_row(self) -> None:
        self._seed_planned_batch_with_run()
        frozen = self._freeze_batch()
        assert frozen.reproduction_checksum is not None

        self.repository._connection.execute(
            "UPDATE planned_runs SET model_parameters_json = ? WHERE run_id = ?",
            ("not-valid-json", "run-001"),
        )
        self.repository._connection.commit()

        report = verify_batch_reproduction(self.repository, "batch-001")
        self.assertFalse(report.verified)
        self.assertEqual(report.status, "invalid_data")
        self.assertEqual(report.stored_checksum, frozen.reproduction_checksum)
        self.assertIsNone(report.computed_checksum)

    def test_verify_reproduction_reports_invalid_batch_row(self) -> None:
        self._seed_planned_batch_with_run()
        self._freeze_batch()

        self.repository._connection.execute(
            "UPDATE benchmark_batches SET operator = ? WHERE batch_id = ?",
            ("", "batch-001"),
        )
        self.repository._connection.commit()

        report = verify_batch_reproduction(self.repository, "batch-001")
        self.assertFalse(report.verified)
        self.assertEqual(report.status, "invalid_data")
        self.assertIsNone(report.stored_checksum)
        self.assertIsNone(report.computed_checksum)

    def test_cli_batch_reproduce_invalid_data_exits_nonzero(self) -> None:
        self._seed_planned_batch_with_run()
        self._freeze_batch()
        self.repository._connection.execute(
            "UPDATE planned_runs SET model_parameters_json = ? WHERE run_id = ?",
            ("not-valid-json", "run-001"),
        )
        self.repository._connection.commit()
        self.repository.close()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(
                [
                    "batch",
                    "reproduce",
                    "--database",
                    str(self.database),
                    "--batch",
                    "batch-001",
                    "--verify-checksum",
                ]
            )
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "invalid_data")
        self.assertFalse(payload["verified"])

    def test_cli_batch_reproduce_invalid_batch_data_exits_nonzero(self) -> None:
        self._seed_planned_batch_with_run()
        self._freeze_batch()
        self.repository._connection.execute(
            "UPDATE benchmark_batches SET operator = ? WHERE batch_id = ?",
            ("", "batch-001"),
        )
        self.repository._connection.commit()
        self.repository.close()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(
                [
                    "batch",
                    "reproduce",
                    "--database",
                    str(self.database),
                    "--batch",
                    "batch-001",
                    "--verify-checksum",
                ]
            )
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "invalid_data")
        self.assertFalse(payload["verified"])

    def test_cli_batch_reproduce_rejects_missing_database_without_creating_it(self) -> None:
        missing_database = Path(self._tmpdir.name) / "typo.db"
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "batch",
                    "reproduce",
                    "--database",
                    str(missing_database),
                    "--batch",
                    "batch-001",
                    "--verify-checksum",
                ]
            )

        self.assertEqual(code, 2)
        self.assertFalse(missing_database.exists())
        self.assertIn("operational database does not exist", stderr.getvalue())

    def test_cli_batch_reproduce_verify_checksum(self) -> None:
        self._seed_planned_batch_with_run()
        frozen = self._freeze_batch()
        self.repository.close()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(
                [
                    "batch",
                    "reproduce",
                    "--database",
                    str(self.database),
                    "--batch",
                    "batch-001",
                    "--verify-checksum",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["verified"])
        self.assertEqual(payload["stored_checksum"], frozen.reproduction_checksum)

    def test_cli_batch_reproduce_mismatch_exits_nonzero(self) -> None:
        self._seed_planned_batch_with_run()
        self._freeze_batch()
        self.repository._connection.execute(
            "UPDATE planned_runs SET exact_model_identifier = ? WHERE run_id = ?",
            ("tampered-model", "run-001"),
        )
        self.repository._connection.commit()
        self.repository.close()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(
                [
                    "batch",
                    "reproduce",
                    "--database",
                    str(self.database),
                    "--batch",
                    "batch-001",
                    "--verify-checksum",
                ]
            )
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "mismatch")
        self.assertFalse(payload["verified"])

    def test_cli_batch_reproduce_without_verification_reports_mismatch(self) -> None:
        self._seed_planned_batch_with_run()
        self._freeze_batch()
        self.repository._connection.execute(
            "UPDATE planned_runs SET exact_model_identifier = ? WHERE run_id = ?",
            ("tampered-model", "run-001"),
        )
        self.repository._connection.commit()
        self.repository.close()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(
                [
                    "batch",
                    "reproduce",
                    "--database",
                    str(self.database),
                    "--batch",
                    "batch-001",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "mismatch")
        self.assertFalse(payload["verified"])

    def test_boundary_rejects_frozen_without_checksum_and_nonfrozen_with_checksum(
        self,
    ) -> None:
        with self.assertRaisesRegex(Exception, "reproduction_checksum"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump()
                | {
                    "status": BatchStatus.FROZEN.value,
                    "started_at": STARTED.isoformat(),
                    "completed_at": COMPLETED.isoformat(),
                    "reproduction_checksum": None,
                }
            )
        with self.assertRaisesRegex(Exception, "reproduction_checksum"):
            BenchmarkBatch.model_validate(
                planned_batch().model_dump() | {"reproduction_checksum": "d" * 64}
            )


if __name__ == "__main__":
    unittest.main()
