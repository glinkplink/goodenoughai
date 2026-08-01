"""Batch lifecycle transitions through completion."""

from __future__ import annotations

from datetime import datetime, timezone

from goodenough_bench.boundaries import BatchStatus, BenchmarkBatch, PlannedRun
from goodenough_bench.exceptions import BatchLifecycleError

ALLOWED_TRANSITIONS: dict[BatchStatus, frozenset[BatchStatus]] = {
    BatchStatus.PLANNED: frozenset({BatchStatus.RUNNING}),
    BatchStatus.RUNNING: frozenset({BatchStatus.COMPLETED}),
    BatchStatus.COMPLETED: frozenset(),
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


def apply_batch_transition(
    batch: BenchmarkBatch,
    new_status: BatchStatus,
    *,
    planned_runs: list[PlannedRun],
    at: datetime | None = None,
    invalid_run_count: int | None = None,
    valid_for_scoring_count: int | None = None,
) -> BenchmarkBatch:
    """Return a valid batch after one allowed transition through completion."""
    if not isinstance(new_status, BatchStatus):
        raise BatchLifecycleError("new_status must be a BatchStatus")
    if new_status not in ALLOWED_TRANSITIONS[batch.status]:
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
    elif new_status is BatchStatus.COMPLETED:
        completed_at = _require_utc_now(at)
        if batch.started_at is not None and completed_at < batch.started_at:
            raise BatchLifecycleError("completed_at cannot precede started_at")
        updates["completed_at"] = completed_at
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

    return BenchmarkBatch.model_validate(batch.model_dump(mode="python") | updates)
