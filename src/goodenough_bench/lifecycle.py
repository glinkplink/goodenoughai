"""Batch lifecycle transitions: planned → running → completed → frozen."""

from __future__ import annotations

from datetime import datetime, timezone

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
        updates["started_at"] = _require_utc_now(at)
        updates["completed_at"] = None
        updates["reproduction_checksum"] = None
    elif new_status is BatchStatus.COMPLETED:
        completed_at = _require_utc_now(at)
        if batch.started_at is not None and completed_at < batch.started_at:
            raise BatchLifecycleError("completed_at cannot precede started_at")
        updates["completed_at"] = completed_at
        updates["reproduction_checksum"] = None
        if invalid_run_count is not None:
            if invalid_run_count < 0:
                raise BatchLifecycleError("invalid_run_count must be >= 0")
            updates["invalid_run_count"] = invalid_run_count
        if valid_for_scoring_count is not None:
            if valid_for_scoring_count < 0:
                raise BatchLifecycleError("valid_for_scoring_count must be >= 0")
            updates["valid_for_scoring_count"] = valid_for_scoring_count
    elif new_status is BatchStatus.FROZEN:
        if not planned_runs:
            raise BatchLifecycleError(
                f"cannot freeze batch {batch.batch_id!r} without at least one planned run"
            )
        if at is not None:
            raise BatchLifecycleError("freeze does not accept a transition timestamp")
        if invalid_run_count is not None or valid_for_scoring_count is not None:
            raise BatchLifecycleError("freeze does not accept run-count updates")
        incomplete_runs = [
            run.run_id for run in planned_runs if not run.profile_provenance_complete
        ]
        if incomplete_runs:
            joined = ", ".join(incomplete_runs)
            raise BatchLifecycleError(
                f"cannot freeze batch {batch.batch_id!r} with incomplete planned-run "
                f"provenance: {joined}"
            )
        # Compute checksum against the completed configuration (pre-freeze fields).
        updates["reproduction_checksum"] = compute_reproduction_checksum(
            batch, planned_runs
        )

    return batch.model_copy(update=updates)
