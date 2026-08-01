"""Deterministic fake-provider fixtures for resumable batch-planning tests."""

from __future__ import annotations

from goodenough_bench.boundaries import (
    BatchPurpose,
    BatchStatus,
    BenchmarkBatch,
    ExecutionEnvironment,
    IdentityConfidence,
    ModelParameters,
    ModelProfileReference,
    ProviderSurface,
    SourceType,
)
from goodenough_bench.planning import (
    BatchPlanResult,
    BatchPlanSpec,
    PlanCaseRef,
    RepositoryBatchPlanner,
)
from goodenough_bench.repository import Repository

CHECKSUM = "a" * 64
DATASET_COMMIT = "b" * 40
RUNNER_COMMIT = "c" * 40


def fake_model_parameters() -> ModelParameters:
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


def fake_batch(*, batch_id: str = "batch-fake-001", run_order_seed: int = 42) -> BenchmarkBatch:
    return BenchmarkBatch(
        batch_id=batch_id,
        batch_purpose=BatchPurpose.DIAGNOSTIC_PILOT,
        dataset_version="automation-mvp-v0.1.0",
        dataset_commit=DATASET_COMMIT,
        runner_commit=RUNNER_COMMIT,
        prompt_version="automation-prompt-v0.1.0",
        run_order_seed=run_order_seed,
        operator="fake-operator",
        environment="fake-test",
        status=BatchStatus.PLANNED,
        started_at=None,
        completed_at=None,
        invalid_run_count=0,
        valid_for_scoring_count=0,
    )


def fake_model_profiles() -> list[ModelProfileReference]:
    return [
        ModelProfileReference(
            model_profile_id="fake-qwen",
            exact_model_identifier="qwen3.5:9b",
            displayed_model_name="Fake Qwen 3.5 9B",
            provider="ollama",
            provider_surface=ProviderSurface.OLLAMA_LOCAL,
            provider_host="localhost",
            source_type=SourceType.LOCAL_EXACT,
            collection_method="goodenough-fake-provider/0.1.0",
            model_identity_confidence=IdentityConfidence.HIGH,
            execution_environment=ExecutionEnvironment.LOCAL,
            runtime="fake-ollama 0.32.5",
            quantization="Q4_K_M",
            hardware_profile_id="fake-hardware-001",
            pricing_snapshot_id=None,
            model_parameters=fake_model_parameters(),
        ),
        ModelProfileReference(
            model_profile_id="fake-gemma",
            exact_model_identifier="gemma4:12b",
            displayed_model_name="Fake Gemma 4 12B",
            provider="ollama",
            provider_surface=ProviderSurface.OLLAMA_LOCAL,
            provider_host="localhost",
            source_type=SourceType.LOCAL_EXACT,
            collection_method="goodenough-fake-provider/0.1.0",
            model_identity_confidence=IdentityConfidence.HIGH,
            execution_environment=ExecutionEnvironment.LOCAL,
            runtime="fake-ollama 0.32.5",
            quantization="Q4_K_M",
            hardware_profile_id="fake-hardware-001",
            pricing_snapshot_id=None,
            model_parameters=fake_model_parameters(),
        ),
    ]


def fake_cases() -> list[PlanCaseRef]:
    return [
        PlanCaseRef(
            case_id="fake.extraction.001",
            case_version="0.1.0",
            prompt_hash=CHECKSUM,
        ),
        PlanCaseRef(
            case_id="fake.classification.001",
            case_version="0.1.0",
            prompt_hash="d" * 64,
        ),
        PlanCaseRef(
            case_id="fake.normalization.001",
            case_version="0.1.0",
            prompt_hash="e" * 64,
        ),
    ]


def fake_batch_plan_spec(
    *,
    batch_id: str = "batch-fake-001",
    run_order_seed: int = 42,
    repetitions: int = 3,
) -> BatchPlanSpec:
    return BatchPlanSpec(
        batch=fake_batch(batch_id=batch_id, run_order_seed=run_order_seed),
        cases=fake_cases(),
        model_profiles=fake_model_profiles(),
        repetitions=repetitions,
    )


class FakeProviderBatchPlanner:
    """Test harness that simulates planning interruption via persist limits."""

    def __init__(self, repository: Repository) -> None:
        self._planner = RepositoryBatchPlanner(repository)

    def plan_until_interrupt(
        self,
        spec: BatchPlanSpec,
        *,
        interrupt_after: int,
    ) -> BatchPlanResult:
        return self._planner.plan_batch(spec, persist_limit=interrupt_after)

    def resume(self, spec: BatchPlanSpec) -> BatchPlanResult:
        return self._planner.plan_batch(spec)
