from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

import goodenough_bench
from goodenough_bench.exceptions import RepositoryConflictError
from goodenough_bench.boundaries import BatchStatus
from goodenough_bench.fake_provider import (
    CHECKSUM,
    fake_batch_plan_spec,
    fake_cases,
    fake_model_profiles,
    FakeProviderBatchPlanner,
)
from goodenough_bench.planning import (
    BatchPlanSpec,
    PlanCaseRef,
    RepositoryBatchPlanner,
    build_planned_run,
    iter_plan_slots,
    stable_planned_run_id,
)
from goodenough_bench.profile_loaders import load_model_profiles
from goodenough_bench.repository import SQLiteRepository


class BatchPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.database = Path(self._tmpdir.name) / "test.db"
        self.repository = SQLiteRepository.from_database(self.database)
        self.planner = RepositoryBatchPlanner(self.repository)
        self.fake = FakeProviderBatchPlanner(self.repository)
        self.spec = fake_batch_plan_spec()

    def tearDown(self) -> None:
        self.repository.close()
        self._tmpdir.cleanup()

    def _expected_identities(self, spec: BatchPlanSpec) -> list[tuple[str, str, int]]:
        return [
            (slot.model_profile_id, slot.case_id, slot.rep_index)
            for slot in iter_plan_slots(spec)
        ]

    def _expected_run_ids(self, spec: BatchPlanSpec) -> list[str]:
        profiles = {profile.model_profile_id: profile for profile in spec.model_profiles}
        cases = {case.case_id: case for case in spec.cases}
        return [
            build_planned_run(
                spec.batch,
                profiles[slot.model_profile_id],
                cases[slot.case_id],
                slot.rep_index,
            ).run_id
            for slot in iter_plan_slots(spec)
        ]

    def test_complete_fake_batch_plan_produces_expected_identities(self) -> None:
        result = self.planner.plan_batch(self.spec)
        stored = self.repository.list_planned_runs_for_batch(self.spec.batch.batch_id)

        self.assertTrue(result.completed)
        self.assertEqual(result.expected_run_count, 18)
        self.assertEqual(result.newly_persisted_count, 18)
        self.assertEqual(len(stored), 18)
        self.assertEqual(
            [(run.model_profile_id, run.case_id, run.rep_index) for run in stored],
            sorted(
                self._expected_identities(self.spec),
                key=lambda item: (item[2], item[0], item[1]),
            ),
        )
        self.assertEqual([run.run_id for run in result.planned_runs], self._expected_run_ids(self.spec))

    def test_identical_plan_is_idempotent(self) -> None:
        first = self.planner.plan_batch(self.spec)
        second = self.planner.plan_batch(self.spec)
        stored = self.repository.list_planned_runs_for_batch(self.spec.batch.batch_id)

        self.assertTrue(first.completed)
        self.assertTrue(second.completed)
        self.assertEqual(first.newly_persisted_count, 18)
        self.assertEqual(second.newly_persisted_count, 0)
        self.assertEqual(len(stored), 18)
        self.assertEqual(
            [run.run_id for run in first.planned_runs],
            [run.run_id for run in second.planned_runs],
        )

    def test_interruption_persists_only_subset(self) -> None:
        interrupted = self.fake.plan_until_interrupt(self.spec, interrupt_after=5)
        stored = self.repository.list_planned_runs_for_batch(self.spec.batch.batch_id)

        self.assertFalse(interrupted.completed)
        self.assertEqual(interrupted.newly_persisted_count, 5)
        self.assertEqual(len(stored), 5)
        self.assertEqual(
            [run.run_id for run in interrupted.planned_runs],
            self._expected_run_ids(self.spec)[:5],
        )

    def test_resume_creates_only_missing_runs(self) -> None:
        interrupted = self.fake.plan_until_interrupt(self.spec, interrupt_after=7)
        resumed = self.fake.resume(self.spec)
        stored = self.repository.list_planned_runs_for_batch(self.spec.batch.batch_id)
        expected_run_ids = set(self._expected_run_ids(self.spec))

        self.assertFalse(interrupted.completed)
        self.assertTrue(resumed.completed)
        self.assertEqual(interrupted.newly_persisted_count, 7)
        self.assertEqual(resumed.newly_persisted_count, 11)
        self.assertEqual(len(stored), 18)
        self.assertEqual({run.run_id for run in stored}, expected_run_ids)
        self.assertEqual(
            [run.run_id for run in resumed.planned_runs],
            self._expected_run_ids(self.spec),
        )

    def test_changed_plan_input_conflicts_with_existing_identity(self) -> None:
        self.planner.plan_batch(self.spec)
        changed_case = PlanCaseRef(
            case_id="fake.extraction.001",
            case_version="0.1.0",
            prompt_hash="f" * 64,
        )
        conflict_spec = self.spec.model_copy(
            update={
                "cases": [
                    changed_case,
                    fake_cases()[1],
                    fake_cases()[2],
                ]
            }
        )
        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.planner.plan_batch(conflict_spec)

    def test_parent_batch_provenance_conflict_still_rejected(self) -> None:
        self.planner.plan_batch(self.spec)
        conflict_spec = self.spec.model_copy(
            update={
                "batch": self.spec.batch.model_copy(update={"dataset_commit": "f" * 40})
            }
        )
        with self.assertRaisesRegex(RepositoryConflictError, "conflicting data"):
            self.planner.plan_batch(conflict_spec)

    def test_planning_is_deterministic_for_same_seed_and_inputs(self) -> None:
        first = self.planner.plan_batch(self.spec)
        replay = self.planner.plan_batch(self.spec)
        other_batch_spec = fake_batch_plan_spec(batch_id="batch-fake-002", run_order_seed=42)
        other_batch = self.planner.plan_batch(other_batch_spec)

        self.assertEqual(
            [(slot.model_profile_id, slot.case_id, slot.rep_index) for slot in iter_plan_slots(self.spec)],
            [(slot.model_profile_id, slot.case_id, slot.rep_index) for slot in iter_plan_slots(other_batch_spec)],
        )
        self.assertEqual([run.run_id for run in first.planned_runs], [run.run_id for run in replay.planned_runs])
        self.assertNotEqual(
            [run.run_id for run in first.planned_runs],
            [run.run_id for run in other_batch.planned_runs],
        )

    def test_stable_run_id_matches_identity(self) -> None:
        run_id = stable_planned_run_id(
            "batch-fake-001",
            "fake-qwen",
            "fake.extraction.001",
            0,
        )
        self.assertTrue(run_id.startswith("run-"))
        self.assertEqual(len(run_id), 68)
        self.assertEqual(
            run_id,
            stable_planned_run_id(
                "batch-fake-001",
                "fake-qwen",
                "fake.extraction.001",
                0,
            ),
        )
        self.assertNotEqual(
            run_id,
            stable_planned_run_id(
                "batch-fake-001",
                "fake-qwen",
                "fake.extraction.001",
                1,
            ),
        )

    def test_planned_runs_inherit_batch_provenance(self) -> None:
        result = self.planner.plan_batch(self.spec)
        batch = result.batch
        for run in result.planned_runs:
            self.assertEqual(run.dataset_version, batch.dataset_version)
            self.assertEqual(run.dataset_commit, batch.dataset_commit)
            self.assertEqual(run.runner_commit, batch.runner_commit)
            self.assertEqual(run.prompt_version, batch.prompt_version)
            self.assertEqual(run.run_order_seed, batch.run_order_seed)
            self.assertTrue(run.profile_provenance_complete)
            self.assertIsNotNone(run.local_model_identity)
            self.assertIsNone(run.routed_provider_identity)

    def test_openrouter_route_identity_is_copied_into_planned_run(self) -> None:
        profile = load_model_profiles().profile_by_id()[
            "synthetic-openrouter-deepseek-v4-flash-api"
        ]

        run = build_planned_run(self.spec.batch, profile, self.spec.cases[0], 0)

        self.assertTrue(run.profile_provenance_complete)
        self.assertIsNone(run.local_model_identity)
        self.assertEqual(run.routed_provider_identity, profile.routed_provider_identity)

    def test_resume_preserves_original_order_and_identities(self) -> None:
        interrupted = self.fake.plan_until_interrupt(self.spec, interrupt_after=3)
        resumed = self.fake.resume(self.spec)
        expected = self._expected_run_ids(self.spec)

        self.assertEqual([run.run_id for run in interrupted.planned_runs], expected[:3])
        self.assertEqual([run.run_id for run in resumed.planned_runs], expected)

    def test_plan_spec_rejects_duplicate_case_ids(self) -> None:
        duplicate = fake_cases()[0].model_copy(update={"prompt_hash": "f" * 64})
        with self.assertRaisesRegex(ValidationError, "unique case_id"):
            BatchPlanSpec(
                batch=self.spec.batch,
                cases=[fake_cases()[0], duplicate],
                model_profiles=self.spec.model_profiles,
                repetitions=3,
            )

    def test_plan_spec_rejects_duplicate_model_profile_ids(self) -> None:
        profiles = fake_model_profiles()
        duplicate = profiles[0].model_copy(update={"displayed_model_name": "Duplicate"})
        with self.assertRaisesRegex(ValidationError, "unique model_profile_id"):
            BatchPlanSpec(
                batch=self.spec.batch,
                cases=self.spec.cases,
                model_profiles=[profiles[0], duplicate],
                repetitions=3,
            )

    def test_plan_spec_requires_inputs_and_positive_repetitions(self) -> None:
        updates: tuple[dict[str, object], ...] = (
            {"cases": []},
            {"model_profiles": []},
            {"repetitions": 0},
        )
        for update in updates:
            with self.subTest(update=update), self.assertRaises(ValidationError):
                BatchPlanSpec.model_validate(
                    self.spec.model_copy(update=update).model_dump()
                )

    def test_plan_spec_requires_a_planned_batch(self) -> None:
        running_batch = self.spec.batch.model_copy(
            update={
                "status": BatchStatus.RUNNING,
                "started_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
            }
        )
        with self.assertRaisesRegex(ValidationError, "status='planned'"):
            BatchPlanSpec(
                batch=running_batch,
                cases=self.spec.cases,
                model_profiles=self.spec.model_profiles,
                repetitions=self.spec.repetitions,
            )

    def test_negative_persist_limit_is_rejected_before_persistence(self) -> None:
        with self.assertRaisesRegex(ValueError, "persist_limit"):
            self.planner.plan_batch(self.spec, persist_limit=-1)
        self.assertIsNone(self.repository.get_batch(self.spec.batch.batch_id))

    def test_package_root_preserves_existing_and_new_public_exports(self) -> None:
        expected = {
            "ErrorType",
            "ParseBoundaryRecord",
            "artifact_ref_for_body",
            "BatchPlanResult",
            "BatchPlanSpec",
            "PlanSlot",
            "RepositoryBatchPlanner",
        }
        self.assertTrue(expected.issubset(set(goodenough_bench.__all__)))
        for name in expected:
            self.assertTrue(hasattr(goodenough_bench, name), name)


if __name__ == "__main__":
    unittest.main()
