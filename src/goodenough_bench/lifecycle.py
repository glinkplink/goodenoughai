"""Batch lifecycle transitions: planned → running → completed → frozen."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError

from goodenough_bench.boundaries import BatchStatus, BenchmarkBatch, PlannedRun
from goodenough_bench.exceptions import BatchLifecycleError
from goodenough_bench.reproduction import compute_reproduction_checksum

ALLOWED_TRANSITIONS: dict[BatchStatus, frozenset[BatchStatus]] = {
    BatchStatus.PLANNED: frozenset({BatchStatus.RUNNING}),
    BatchStatus.RUNNING: frozenset({BatchStatus.COMPLETED}),
    BatchStatus.COMPLETED: frozenset({BatchStatus.FROZEN}),
    BatchStatus.FROZEN: frozenset(),
}


def _require_utc_now(at: datetime | None) -> datetime:
    if at is None:
        return datetime.now(timezone.utc)
    if at.tzinfo is None or at.utcoffset() is None:
        raise BatchLifecycleError("transition timestamp must include a UTC offset")
    if at.utcoffset() != timezone.utc.utcoffset(at):
        raise BatchLifecycleError("transition timestamp must be UTC")
    return at


def _planned_run_batch_provenance_mismatches(
    batch: BenchmarkBatch,
    run: PlannedRun,
) -> list[str]:
    mismatches: list[str] = []
    if run.dataset_version != batch.dataset_version:
        mismatches.append("dataset_version")
    if run.dataset_commit != batch.dataset_commit:
        mismatches.append("dataset_commit")
    if run.runner_commit != batch.runner_commit:
        mismatches.append("runner_commit")
    if run.prompt_version != batch.prompt_version:
        mismatches.append("prompt_version")
    if run.run_order_seed != batch.run_order_seed:
        mismatches.append("run_order_seed")
    return mismatches


def _validated_freeze_planned_runs(
    batch: BenchmarkBatch,
    planned_runs: list[PlannedRun],
) -> list[PlannedRun]:
    if not planned_runs:
        raise BatchLifecycleError(
            f"cannot freeze batch {batch.batch_id!r} without at least one planned run"
        )

    validated: list[PlannedRun] = []
    for run in planned_runs:
        try:
            revalidated = PlannedRun.model_validate(run.model_dump(mode="python"))
        except ValidationError as error:
            run_id = getattr(run, "run_id", None)
            label = (
                f"planned run {run_id!r}"
                if run_id is not None
                else "constructed planned run"
            )
            raise BatchLifecycleError(
                f"{label} failed full boundary validation: {error}"
            ) from error
        if revalidated.batch_id != batch.batch_id:
            raise BatchLifecycleError(
                f"planned run {revalidated.run_id!r} belongs to batch "
                f"{revalidated.batch_id!r}, not {batch.batch_id!r}"
            )
        mismatches = _planned_run_batch_provenance_mismatches(batch, revalidated)
        if mismatches:
            fields = ", ".join(mismatches)
            raise BatchLifecycleError(
                f"planned run {revalidated.run_id!r} provenance conflicts with parent "
                f"batch {batch.batch_id!r} for: {fields}"
            )
        if not revalidated.profile_provenance_complete:
            raise BatchLifecycleError(
                f"cannot freeze batch {batch.batch_id!r} with incomplete planned-run "
                f"provenance: {revalidated.run_id}"
            )
        validated.append(revalidated)
    return validated


def apply_batch_transition(
    batch: BenchmarkBatch,
    new_status: BatchStatus,
    *,
    planned_runs: list[PlannedRun],
    at: datetime | None = None,
    invalid_run_count: int | None = None,
    valid_for_scoring_count: int | None = None,
) -> BenchmarkBatch:
    """Return a new batch after applying an allowed lifecycle transition."""
    if not isinstance(new_status, BatchStatus):
        raise BatchLifecycleError("new_status must be a BatchStatus")
    allowed = ALLOWED_TRANSITIONS[batch.status]
    if new_status not in allowed:
        raise BatchLifecycleError(
            f"cannot transition batch {batch.batch_id!r} from "
            f"{batch.status.value!r} to {new_status.value!r}"
        )

    updates: dict[str, object] = {"status": new_status}

    if new_status is BatchStatus.RUNNING:
        if invalid_run_count is not None or valid_for_scoring_count is not None:
            raise BatchLifecycleError(
                "run-count updates are allowed only when completing a batch"
            )
        if batch.invalid_run_count != 0 or batch.valid_for_scoring_count != 0:
            raise BatchLifecycleError(
                "running batches require invalid_run_count and "
                "valid_for_scoring_count to be 0"
            )
        updates["started_at"] = _require_utc_now(at)
        updates["completed_at"] = None
        updates["reproduction_checksum"] = None
    elif new_status is BatchStatus.COMPLETED:
        completed_at = _require_utc_now(at)
        if batch.started_at is not None and completed_at < batch.started_at:
            raise BatchLifecycleError("completed_at cannot precede started_at")
        updates["completed_at"] = completed_at
        updates["reproduction_checksum"] = None
        if invalid_run_count is None or valid_for_scoring_count is None:
            raise BatchLifecycleError(
                "invalid_run_count and valid_for_scoring_count are required "
                "when completing a batch"
            )
        if invalid_run_count < 0:
            raise BatchLifecycleError("invalid_run_count must be >= 0")
        if valid_for_scoring_count < 0:
            raise BatchLifecycleError("valid_for_scoring_count must be >= 0")
        updates["invalid_run_count"] = invalid_run_count
        updates["valid_for_scoring_count"] = valid_for_scoring_count
        accounted = invalid_run_count + valid_for_scoring_count
        planned_count = len(planned_runs)
        if accounted != planned_count:
            raise BatchLifecycleError(
                f"completion run counts must account for all {planned_count} "
                f"planned run(s); invalid_run_count + valid_for_scoring_count = "
                f"{accounted}"
            )
    elif new_status is BatchStatus.FROZEN:
        if at is not None:
            raise BatchLifecycleError("freeze does not accept a transition timestamp")
        if invalid_run_count is not None or valid_for_scoring_count is not None:
            raise BatchLifecycleError("freeze does not accept run-count updates")
        validated_runs = _validated_freeze_planned_runs(batch, planned_runs)
        updates["reproduction_checksum"] = compute_reproduction_checksum(
            batch, validated_runs
        )

    return batch.model_copy(update=updates)
