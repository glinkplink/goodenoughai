"""Deterministic, resumable batch planning for planned-run persistence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pydantic import Field, model_validator

from goodenough_bench.boundaries import (
    BatchStatus,
    BenchmarkBatch,
    BoundaryModel,
    Identifier,
    ModelProfileReference,
    PlannedRun,
    SemVer,
    Sha256,
)
from goodenough_bench.repository import Repository


class PlanCaseRef(BoundaryModel):
    """Minimal case reference for planning; full cases are not required."""

    case_id: Identifier
    case_version: SemVer
    prompt_hash: Sha256


class BatchPlanSpec(BoundaryModel):
    """Explicit inputs that fully determine a batch's planned-run set."""

    batch: BenchmarkBatch
    cases: list[PlanCaseRef] = Field(min_length=1)
    model_profiles: list[ModelProfileReference] = Field(min_length=1)
    repetitions: int = Field(default=3, ge=1)

    @model_validator(mode="after")
    def require_unique_planning_inputs(self) -> BatchPlanSpec:
        if self.batch.status is not BatchStatus.PLANNED:
            raise ValueError("batch planning requires batch.status='planned'")
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("planning cases must have unique case_id values")
        profile_ids = [profile.model_profile_id for profile in self.model_profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError(
                "planning model profiles must have unique model_profile_id values"
            )
        return self


@dataclass(frozen=True)
class PlanSlot:
    """One planned-run position in deterministic execution order."""

    model_profile_id: str
    case_id: str
    rep_index: int


@dataclass(frozen=True)
class BatchPlanResult:
    """Outcome of one planning invocation."""

    batch: BenchmarkBatch
    planned_runs: list[PlannedRun]
    expected_run_count: int
    newly_persisted_count: int
    completed: bool


def stable_planned_run_id(
    batch_id: str,
    model_profile_id: str,
    case_id: str,
    rep_index: int,
) -> str:
    """Derive a deterministic run_id from the stable planned-run identity."""
    identity = json.dumps(
        [batch_id, model_profile_id, case_id, rep_index],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode()
    digest = hashlib.sha256(identity).hexdigest()
    return f"run-{digest}"


def _rep_case_order(run_order_seed: int, rep_index: int, case_ids: list[str]) -> list[str]:
    """Order cases by a portable hash of the seed, round, and case identity."""

    def order_key(case_id: str) -> tuple[bytes, str]:
        material = f"{run_order_seed}\0{rep_index}\0{case_id}".encode()
        return hashlib.sha256(material).digest(), case_id

    return sorted(case_ids, key=order_key)


def iter_plan_slots(spec: BatchPlanSpec) -> list[PlanSlot]:
    """Return the full planned-run sequence in deterministic execution order."""
    case_ids = [case.case_id for case in spec.cases]
    profile_ids = [profile.model_profile_id for profile in spec.model_profiles]
    slots: list[PlanSlot] = []
    for rep_index in range(spec.repetitions):
        for model_profile_id in profile_ids:
            for case_id in _rep_case_order(spec.batch.run_order_seed, rep_index, case_ids):
                slots.append(
                    PlanSlot(
                        model_profile_id=model_profile_id,
                        case_id=case_id,
                        rep_index=rep_index,
                    )
                )
    return slots


def _case_by_id(spec: BatchPlanSpec) -> dict[str, PlanCaseRef]:
    return {case.case_id: case for case in spec.cases}


def _profile_by_id(spec: BatchPlanSpec) -> dict[str, ModelProfileReference]:
    return {profile.model_profile_id: profile for profile in spec.model_profiles}


def build_planned_run(
    batch: BenchmarkBatch,
    profile: ModelProfileReference,
    case: PlanCaseRef,
    rep_index: int,
) -> PlannedRun:
    """Construct a planned run consistent with parent batch provenance."""
    return PlannedRun(
        run_id=stable_planned_run_id(
            batch.batch_id,
            profile.model_profile_id,
            case.case_id,
            rep_index,
        ),
        batch_id=batch.batch_id,
        case_id=case.case_id,
        case_version=case.case_version,
        model_profile_id=profile.model_profile_id,
        rep_index=rep_index,
        run_order_seed=batch.run_order_seed,
        dataset_version=batch.dataset_version,
        dataset_commit=batch.dataset_commit,
        runner_commit=batch.runner_commit,
        prompt_version=batch.prompt_version,
        prompt_hash=case.prompt_hash,
        exact_model_identifier=profile.exact_model_identifier,
        displayed_model_name=profile.displayed_model_name,
        provider=profile.provider,
        provider_surface=profile.provider_surface,
        provider_host=profile.provider_host,
        collection_method=profile.collection_method,
        model_identity_confidence=profile.model_identity_confidence,
        source_type=profile.source_type,
        execution_environment=profile.execution_environment,
        runtime=profile.runtime,
        quantization=profile.quantization,
        hardware_profile_id=profile.hardware_profile_id,
        local_model_identity=profile.local_model_identity,
        routed_provider_identity=profile.routed_provider_identity,
        profile_provenance_complete=True,
        pricing_snapshot_id=profile.pricing_snapshot_id,
        model_parameters=profile.model_parameters,
    )


@runtime_checkable
class BatchPlanner(Protocol):
    def plan_batch(
        self,
        spec: BatchPlanSpec,
        *,
        persist_limit: int | None = None,
    ) -> BatchPlanResult: ...


class RepositoryBatchPlanner:
    """Persist planned runs through the repository with resume/idempotency."""

    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    def plan_batch(
        self,
        spec: BatchPlanSpec,
        *,
        persist_limit: int | None = None,
    ) -> BatchPlanResult:
        if persist_limit is not None and persist_limit < 0:
            raise ValueError("persist_limit must be greater than or equal to zero")

        batch = self._repository.create_batch(spec.batch)
        cases = _case_by_id(spec)
        profiles = _profile_by_id(spec)
        slots = iter_plan_slots(spec)
        persisted: list[PlannedRun] = []
        newly_persisted = 0

        for index, slot in enumerate(slots):
            if persist_limit is not None and index >= persist_limit:
                break
            profile = profiles[slot.model_profile_id]
            case = cases[slot.case_id]
            planned = build_planned_run(batch, profile, case, slot.rep_index)
            before = self._repository.get_planned_run_by_identity(
                planned.batch_id,
                planned.model_profile_id,
                planned.case_id,
                planned.rep_index,
            )
            stored = self._repository.create_planned_run(planned)
            if before is None:
                newly_persisted += 1
            persisted.append(stored)

        completed = len(persisted) == len(slots)
        return BatchPlanResult(
            batch=batch,
            planned_runs=persisted,
            expected_run_count=len(slots),
            newly_persisted_count=newly_persisted,
            completed=completed,
        )
