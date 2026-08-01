from __future__ import annotations

import json
import tempfile
import unittest
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
from goodenough_bench.exceptions import RepositoryConflictError
from goodenough_bench.profile_loaders import (
    load_model_profiles,
    load_pricing_snapshots,
)
from goodenough_bench.repository import (
    SQLiteRepository,
    canonical_model_parameters_json,
)


CHECKSUM = "a" * 64
DATASET_COMMIT = "b" * 40
RUNNER_COMMIT = "c" * 40


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


def planned_batch(*, batch_purpose: BatchPurpose = BatchPurpose.DIAGNOSTIC_PILOT) -> BenchmarkBatch:
    return BenchmarkBatch(
        batch_id="batch-001",
        batch_purpose=batch_purpose,
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


def api_planned_run(
    *,
    run_id: str = "run-api-001",
    profile_id: str = "synthetic-deepseek-v4-flash-api",
) -> PlannedRun:
    profile = load_model_profiles().profile_by_id()[profile_id]
    return PlannedRun.model_validate(
        {
            **planned_run(run_id=run_id).model_dump(mode="python"),
            **profile.model_dump(
                mode="python",
                include=set(ModelProfileReference.model_fields),
            ),
        }
    )


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.database = Path(self._tmpdir.name) / "test.db"
        self.repository = SQLiteRepository.from_database(self.database)

    def tearDown(self) -> None:
        self.repository.close()
        self._tmpdir.cleanup()

    def test_batch_purpose_sqlite_round_trip(self) -> None:
        for purpose in BatchPurpose:
            batch = planned_batch(batch_purpose=purpose).model_copy(
                update={"batch_id": f"batch-{purpose.value}"}
            )
            created = self.repository.create_batch(batch)
            fetched = self.repository.get_batch(batch.batch_id)
            self.assertEqual(created.batch_purpose, purpose)
            assert fetched is not None
            self.assertEqual(fetched.batch_purpose, purpose)

    def test_batch_persistence_and_retrieval(self) -> None:
        batch = planned_batch()
        created = self.repository.create_batch(batch)
        fetched = self.repository.get_batch(batch.batch_id)

        self.assertEqual(created, batch)
        self.assertEqual(fetched, batch)

    def test_idempotent_identical_batch_creation(self) -> None:
        batch = planned_batch()
        first = self.repository.create_batch(batch)
        second = self.repository.create_batch(batch)
        self.assertIsNotNone(first)
        self.assertEqual(first, second)

    def test_conflicting_batch_reuse_rejection(self) -> None:
        batch = planned_batch()
        self.repository.create_batch(batch)
        conflict = batch.model_copy(update={"operator": "operator-2"})
        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.repository.create_batch(conflict)

    def test_revalidates_copied_batch_before_any_insert(self) -> None:
        invalid = planned_batch().model_copy(
            update={"reproduction_checksum": "d" * 64}
        )

        with self.assertRaisesRegex(
            RepositoryConflictError, "failed full boundary validation"
        ):
            self.repository.create_batch(invalid)

        self.assertIsNone(self.repository.get_batch(invalid.batch_id))

    def test_full_planned_run_round_trip(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        created = self.repository.create_planned_run(run)
        fetched = self.repository.get_planned_run(run.run_id)
        by_identity = self.repository.get_planned_run_by_identity(
            run.batch_id,
            run.model_profile_id,
            run.case_id,
            run.rep_index,
        )

        self.assertEqual(created, run)
        self.assertEqual(fetched, run)
        assert fetched is not None
        self.assertEqual(fetched.local_model_identity, run.local_model_identity)
        self.assertTrue(fetched.profile_provenance_complete)
        self.assertEqual(by_identity, run)

    def test_enum_round_trip(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        fetched = self.repository.get_planned_run(run.run_id)
        assert fetched is not None
        self.assertEqual(fetched.provider_surface, ProviderSurface.OLLAMA_LOCAL)
        self.assertEqual(fetched.source_type, SourceType.LOCAL_EXACT)
        self.assertEqual(fetched.execution_environment, ExecutionEnvironment.LOCAL)
        self.assertEqual(fetched.model_identity_confidence, IdentityConfidence.HIGH)

    def test_utc_timestamp_handling_for_batches(self) -> None:
        started = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 31, 13, 0, tzinfo=timezone.utc)
        batch = planned_batch().model_copy(
            update={
                "status": BatchStatus.COMPLETED,
                "started_at": started,
                "completed_at": completed,
                "valid_for_scoring_count": 3,
            }
        )
        self.repository.create_batch(batch)
        fetched = self.repository.get_batch(batch.batch_id)
        assert fetched is not None
        self.assertEqual(fetched.started_at, started)
        self.assertEqual(fetched.completed_at, completed)

    def test_explicit_none_null_provenance_round_trip(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        fetched = self.repository.get_planned_run(run.run_id)
        assert fetched is not None
        self.assertIsNone(fetched.pricing_snapshot_id)

    def test_canonical_model_parameters_json_round_trip(self) -> None:
        params = model_parameters()
        canonical = canonical_model_parameters_json(params)
        self.assertEqual(
            json.loads(canonical),
            {
                "frequency_penalty": None,
                "max_output_tokens": 256,
                "presence_penalty": None,
                "reasoning_mode": None,
                "response_format": "json_schema",
                "seed": None,
                "temperature": 0.0,
                "top_p": None,
            },
        )

        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        fetched = self.repository.get_planned_run(run.run_id)
        assert fetched is not None
        self.assertEqual(
            canonical_model_parameters_json(fetched.model_parameters),
            canonical,
        )

    def test_idempotent_duplicate_planned_run_creation(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        first = self.repository.create_planned_run(run)
        second = self.repository.create_planned_run(run)
        self.assertEqual(first, second)

    def test_conflicting_run_id_on_same_planned_run_identity(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        conflict = run.model_copy(update={"run_id": "run-002"})
        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.repository.create_planned_run(conflict)

    def test_one_differing_provenance_field_on_same_identity(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        conflict = run.model_copy(update={"prompt_hash": "d" * 64})
        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.repository.create_planned_run(conflict)

    def test_one_differing_model_parameters_field_on_same_identity(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        changed_params = model_parameters().model_copy(update={"temperature": 0.1})
        conflict = run.model_copy(update={"model_parameters": changed_params})
        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.repository.create_planned_run(conflict)

    def test_one_differing_local_artifact_identity_conflicts(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        self.repository.create_planned_run(run)
        assert run.local_model_identity is not None
        changed_identity = run.local_model_identity.model_copy(
            update={"artifact_digest": "9" * 64}
        )
        conflict = run.model_copy(update={"local_model_identity": changed_identity})

        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.repository.create_planned_run(conflict)

    def test_new_planned_run_rejects_legacy_incomplete_provenance(self) -> None:
        self.repository.create_batch(planned_batch())
        incomplete = planned_run().model_copy(
            update={
                "local_model_identity": None,
                "profile_provenance_complete": False,
            }
        )

        with self.assertRaisesRegex(RepositoryConflictError, "complete profile provenance"):
            self.repository.create_planned_run(incomplete)

    def test_revalidates_copied_planned_run_before_any_insert(self) -> None:
        self.repository.create_batch(planned_batch())
        invalid = api_planned_run().model_copy(
            update={
                "provider": "openrouter",
                "provider_surface": ProviderSurface.OPENROUTER_API,
                "provider_host": "openrouter.ai",
            }
        )

        with self.assertRaisesRegex(
            RepositoryConflictError,
            "failed full boundary validation",
        ):
            self.repository.create_planned_run(invalid)

        self.assertIsNone(self.repository.get_planned_run(invalid.run_id))

    def test_direct_api_write_requires_pricing_catalog(self) -> None:
        self.repository.create_batch(planned_batch())
        run = api_planned_run()

        with self.assertRaisesRegex(
            RepositoryConflictError,
            "requires a PricingSnapshotCatalog",
        ):
            self.repository.create_planned_run(run)

        self.assertIsNone(self.repository.get_planned_run(run.run_id))

    def test_direct_api_write_resolves_pricing_catalog(self) -> None:
        self.repository.create_batch(planned_batch())
        run = api_planned_run()

        stored = self.repository.create_planned_run(
            run,
            pricing_catalog=load_pricing_snapshots(),
        )

        self.assertEqual(stored, run)

    def test_direct_api_write_rejects_unknown_pricing_snapshot(self) -> None:
        self.repository.create_batch(planned_batch())
        run = api_planned_run().model_copy(
            update={"pricing_snapshot_id": "unknown-pricing-snapshot"}
        )

        with self.assertRaisesRegex(
            RepositoryConflictError,
            "unknown pricing snapshot",
        ):
            self.repository.create_planned_run(
                run,
                pricing_catalog=load_pricing_snapshots(),
            )

        self.assertIsNone(self.repository.get_planned_run(run.run_id))

    def test_direct_api_write_rejects_mismatched_pricing_snapshot(self) -> None:
        self.repository.create_batch(planned_batch())
        run = api_planned_run().model_copy(
            update={
                "pricing_snapshot_id": "synthetic-gpt-5.6-luna-2026-01-01"
            }
        )

        with self.assertRaisesRegex(RepositoryConflictError, "provider"):
            self.repository.create_planned_run(
                run,
                pricing_catalog=load_pricing_snapshots(),
            )

        self.assertIsNone(self.repository.get_planned_run(run.run_id))

    def test_direct_api_write_rejects_exact_model_pricing_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        run = api_planned_run().model_copy(
            update={"exact_model_identifier": "deepseek-other-model"}
        )

        with self.assertRaisesRegex(
            RepositoryConflictError,
            "exact_model_identifier",
        ):
            self.repository.create_planned_run(
                run,
                pricing_catalog=load_pricing_snapshots(),
            )

        self.assertIsNone(self.repository.get_planned_run(run.run_id))

    def test_direct_api_write_rejects_routed_pricing_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        valid = api_planned_run(
            profile_id="synthetic-openrouter-deepseek-v4-flash-api"
        )
        assert valid.routed_provider_identity is not None
        mismatched_route = valid.routed_provider_identity.model_copy(
            update={"upstream_model_identifier": "deepseek-other-model"}
        )
        run = valid.model_copy(
            update={"routed_provider_identity": mismatched_route}
        )

        with self.assertRaisesRegex(
            RepositoryConflictError,
            "routed_provider_identity",
        ):
            self.repository.create_planned_run(
                run,
                pricing_catalog=load_pricing_snapshots(),
            )

        self.assertIsNone(self.repository.get_planned_run(run.run_id))

    def test_reuse_of_one_run_id_for_different_planned_run_identity(self) -> None:
        self.repository.create_batch(planned_batch())
        first = planned_run(run_id="run-shared", rep_index=0)
        self.repository.create_planned_run(first)
        second = planned_run(run_id="run-shared", rep_index=1)
        with self.assertRaisesRegex(
            RepositoryConflictError,
            "already exists for a different planned-run identity",
        ):
            self.repository.create_planned_run(second)

    def test_reject_planned_run_when_batch_does_not_exist(self) -> None:
        with self.assertRaisesRegex(RepositoryConflictError, "does not exist"):
            self.repository.create_planned_run(planned_run())

    def test_reject_planned_run_with_dataset_version_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        conflict = planned_run().model_copy(update={"dataset_version": "automation-mvp-v0.2.0"})
        with self.assertRaisesRegex(RepositoryConflictError, "dataset_version"):
            self.repository.create_planned_run(conflict)

    def test_reject_planned_run_with_dataset_commit_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        conflict = planned_run().model_copy(update={"dataset_commit": "d" * 40})
        with self.assertRaisesRegex(RepositoryConflictError, "dataset_commit"):
            self.repository.create_planned_run(conflict)

    def test_reject_planned_run_with_runner_commit_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        conflict = planned_run().model_copy(update={"runner_commit": "e" * 40})
        with self.assertRaisesRegex(RepositoryConflictError, "runner_commit"):
            self.repository.create_planned_run(conflict)

    def test_reject_planned_run_with_prompt_version_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        conflict = planned_run().model_copy(
            update={"prompt_version": "automation-prompt-v0.2.0"}
        )
        with self.assertRaisesRegex(RepositoryConflictError, "prompt_version"):
            self.repository.create_planned_run(conflict)

    def test_reject_planned_run_with_run_order_seed_mismatch(self) -> None:
        self.repository.create_batch(planned_batch())
        conflict = planned_run().model_copy(update={"run_order_seed": 99})
        with self.assertRaisesRegex(RepositoryConflictError, "run_order_seed"):
            self.repository.create_planned_run(conflict)

    def test_idempotent_planned_run_still_validates_parent_batch_provenance(self) -> None:
        self.repository.create_batch(planned_batch())
        run = planned_run()
        first = self.repository.create_planned_run(run)
        second = self.repository.create_planned_run(run)
        self.assertEqual(first, second)
        mismatch = run.model_copy(update={"dataset_commit": "f" * 40})
        with self.assertRaisesRegex(RepositoryConflictError, "dataset_commit"):
            self.repository.create_planned_run(mismatch)


if __name__ == "__main__":
    unittest.main()
