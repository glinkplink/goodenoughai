"""Deterministic batch reproduction metadata and checksum verification."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import ValidationError

from goodenough_bench.boundaries import (
    BatchStatus,
    BenchmarkBatch,
    BoundaryModel,
    PlannedRun,
    Sha256,
)


def reproduction_payload(
    batch: BenchmarkBatch,
    planned_runs: list[PlannedRun],
) -> dict[str, Any]:
    """Canonical reproduction payload for provenance fingerprinting.

    Covers the batch's persisted provenance and each complete planned-run identity.
    Lifecycle status and the checksum itself are excluded so the value computed
    immediately before freezing can be recomputed from the frozen record.
    Scored ``result_checksum`` values remain a later scoring-phase concern.
    """
    ordered = sorted(
        planned_runs,
        key=lambda run: (run.rep_index, run.model_profile_id, run.case_id, run.run_id),
    )
    batch_provenance = batch.model_dump(
        mode="json",
        exclude={"status", "reproduction_checksum"},
    )
    return {
        "batch": batch_provenance,
        "planned_runs": [run.model_dump(mode="json") for run in ordered],
    }


def compute_reproduction_checksum(
    batch: BenchmarkBatch,
    planned_runs: list[PlannedRun],
) -> Sha256:
    """SHA-256 of canonical JSON for batch + planned-run reproduction metadata."""
    payload = reproduction_payload(batch, planned_runs)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class BatchReproductionReport(BoundaryModel):
    """Machine-readable reproduction verification result."""

    command: Literal["batch reproduce"] = "batch reproduce"
    batch_id: str
    status: Literal["ok", "mismatch", "not_frozen", "not_found", "invalid_data"]
    verified: bool
    stored_checksum: Sha256 | None
    computed_checksum: Sha256 | None


def verify_batch_reproduction(repository: Any, batch_id: str) -> BatchReproductionReport:
    """Recompute reproduction checksum and compare to the frozen batch record."""
    batch = repository.get_batch(batch_id)
    if batch is None:
        return BatchReproductionReport(
            batch_id=batch_id,
            status="not_found",
            verified=False,
            stored_checksum=None,
            computed_checksum=None,
        )
    if batch.status is not BatchStatus.FROZEN or batch.reproduction_checksum is None:
        return BatchReproductionReport(
            batch_id=batch_id,
            status="not_frozen",
            verified=False,
            stored_checksum=batch.reproduction_checksum,
            computed_checksum=None,
        )

    try:
        planned_runs = repository.list_planned_runs_for_batch(batch_id)
        computed = compute_reproduction_checksum(batch, planned_runs)
    except (ValidationError, json.JSONDecodeError, ValueError, TypeError):
        return BatchReproductionReport(
            batch_id=batch_id,
            status="invalid_data",
            verified=False,
            stored_checksum=batch.reproduction_checksum,
            computed_checksum=None,
        )

    verified = computed == batch.reproduction_checksum
    return BatchReproductionReport(
        batch_id=batch_id,
        status="ok" if verified else "mismatch",
        verified=verified,
        stored_checksum=batch.reproduction_checksum,
        computed_checksum=computed,
    )
