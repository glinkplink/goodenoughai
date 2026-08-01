"""Portable repository boundary for benchmark batches and planned runs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import ValidationError

from goodenough_bench.boundaries import (
    BatchPurpose,
    BatchStatus,
    BenchmarkBatch,
    ExecutionEnvironment,
    IdentityConfidence,
    LocalModelIdentity,
    ModelParameters,
    PlannedRun,
    ProviderSurface,
    RoutedProviderIdentity,
    SourceType,
)
from goodenough_bench.db import connect_sqlite, connect_sqlite_readonly
from goodenough_bench.exceptions import BatchLifecycleError, RepositoryConflictError
from goodenough_bench.lifecycle import apply_batch_transition
from goodenough_bench.migrations import apply_migrations, require_current_migrations
from goodenough_bench.profile_loaders import PricingSnapshotCatalog


def canonical_model_parameters_json(model_parameters: ModelParameters) -> str:
    """Serialize ModelParameters with sorted keys and compact separators."""
    return json.dumps(
        model_parameters.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_optional_identity_json(
    identity: LocalModelIdentity | RoutedProviderIdentity | None,
) -> str | None:
    if identity is None:
        return None
    return json.dumps(
        identity.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )


def _datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _datetime_from_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _batch_to_row(batch: BenchmarkBatch) -> tuple[object, ...]:
    return (
        batch.batch_id,
        batch.batch_purpose.value,
        batch.dataset_version,
        batch.dataset_commit,
        batch.runner_commit,
        batch.prompt_version,
        batch.run_order_seed,
        batch.operator,
        batch.environment,
        batch.status.value,
        _datetime_to_iso(batch.started_at),
        _datetime_to_iso(batch.completed_at),
        batch.invalid_run_count,
        batch.valid_for_scoring_count,
        batch.reproduction_checksum,
    )


def _row_to_batch(row: sqlite3.Row) -> BenchmarkBatch:
    return BenchmarkBatch(
        batch_id=row["batch_id"],
        batch_purpose=BatchPurpose(row["batch_purpose"]),
        dataset_version=row["dataset_version"],
        dataset_commit=row["dataset_commit"],
        runner_commit=row["runner_commit"],
        prompt_version=row["prompt_version"],
        run_order_seed=row["run_order_seed"],
        operator=row["operator"],
        environment=row["environment"],
        status=BatchStatus(row["status"]),
        started_at=_datetime_from_iso(row["started_at"]),
        completed_at=_datetime_from_iso(row["completed_at"]),
        invalid_run_count=row["invalid_run_count"],
        valid_for_scoring_count=row["valid_for_scoring_count"],
        reproduction_checksum=(
            row["reproduction_checksum"]
            if "reproduction_checksum" in set(row.keys())
            else None
        ),
    )


def _planned_run_to_row(run: PlannedRun) -> tuple[object, ...]:
    return (
        run.run_id,
        run.batch_id,
        run.case_id,
        run.case_version,
        run.model_profile_id,
        run.rep_index,
        run.run_order_seed,
        run.dataset_version,
        run.dataset_commit,
        run.runner_commit,
        run.prompt_version,
        run.prompt_hash,
        run.exact_model_identifier,
        run.displayed_model_name,
        run.provider,
        run.provider_surface.value,
        run.provider_host,
        run.collection_method,
        run.model_identity_confidence.value,
        run.source_type.value,
        run.execution_environment.value,
        run.runtime,
        run.quantization,
        run.hardware_profile_id,
        _canonical_optional_identity_json(run.local_model_identity),
        _canonical_optional_identity_json(run.routed_provider_identity),
        int(run.profile_provenance_complete),
        run.pricing_snapshot_id,
        canonical_model_parameters_json(run.model_parameters),
    )


def _row_to_planned_run(row: sqlite3.Row) -> PlannedRun:
    return PlannedRun(
        run_id=row["run_id"],
        batch_id=row["batch_id"],
        case_id=row["case_id"],
        case_version=row["case_version"],
        model_profile_id=row["model_profile_id"],
        rep_index=row["rep_index"],
        run_order_seed=row["run_order_seed"],
        dataset_version=row["dataset_version"],
        dataset_commit=row["dataset_commit"],
        runner_commit=row["runner_commit"],
        prompt_version=row["prompt_version"],
        prompt_hash=row["prompt_hash"],
        exact_model_identifier=row["exact_model_identifier"],
        displayed_model_name=row["displayed_model_name"],
        provider=row["provider"],
        provider_surface=ProviderSurface(row["provider_surface"]),
        provider_host=row["provider_host"],
        collection_method=row["collection_method"],
        model_identity_confidence=IdentityConfidence(row["model_identity_confidence"]),
        source_type=SourceType(row["source_type"]),
        execution_environment=ExecutionEnvironment(row["execution_environment"]),
        runtime=row["runtime"],
        quantization=row["quantization"],
        hardware_profile_id=row["hardware_profile_id"],
        local_model_identity=(
            None
            if row["local_model_identity_json"] is None
            else LocalModelIdentity.model_validate_json(row["local_model_identity_json"])
        ),
        routed_provider_identity=(
            None
            if row["routed_provider_identity_json"] is None
            else RoutedProviderIdentity.model_validate_json(
                row["routed_provider_identity_json"]
            )
        ),
        profile_provenance_complete=bool(row["profile_provenance_complete"]),
        model_parameters=ModelParameters.model_validate_json(row["model_parameters_json"]),
        pricing_snapshot_id=row["pricing_snapshot_id"],
    )


def _batches_equal(left: BenchmarkBatch, right: BenchmarkBatch) -> bool:
    return left.model_dump() == right.model_dump()


def _planned_runs_equal(left: PlannedRun, right: PlannedRun) -> bool:
    left_dump = left.model_dump()
    right_dump = right.model_dump()
    left_dump["model_parameters"] = canonical_model_parameters_json(left.model_parameters)
    right_dump["model_parameters"] = canonical_model_parameters_json(right.model_parameters)
    return left_dump == right_dump


def _validate_planned_run_batch_provenance(batch: BenchmarkBatch, run: PlannedRun) -> None:
    """Reject planned runs whose frozen provenance disagrees with the parent batch."""
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
    if mismatches:
        fields = ", ".join(mismatches)
        raise RepositoryConflictError(
            f"planned run {run.run_id!r} provenance conflicts with parent batch "
            f"{batch.batch_id!r} for: {fields}"
        )


def _entity_label(entity: BenchmarkBatch | PlannedRun, *, kind: str, id_field: str) -> str:
    identifier = getattr(entity, id_field, None)
    if identifier is None:
        return f"constructed {kind} (missing {id_field})"
    return f"{kind} {identifier!r}"


def _revalidate_planned_run(run: PlannedRun) -> PlannedRun:
    """Re-run all lifecycle validators bypassed by unsafe Pydantic copies."""
    try:
        return PlannedRun.model_validate(run.model_dump(mode="python"))
    except ValidationError as error:
        raise RepositoryConflictError(
            f"{_entity_label(run, kind='planned run', id_field='run_id')} "
            f"failed full boundary validation: {error}"
        ) from error


def _revalidate_batch(batch: BenchmarkBatch) -> BenchmarkBatch:
    """Re-run lifecycle validators bypassed by unsafe Pydantic copies."""
    try:
        return BenchmarkBatch.model_validate(batch.model_dump(mode="python"))
    except ValidationError as error:
        raise RepositoryConflictError(
            f"{_entity_label(batch, kind='batch', id_field='batch_id')} "
            f"failed full boundary validation: {error}"
        ) from error


def _validate_planned_run_pricing(
    run: PlannedRun,
    pricing_catalog: PricingSnapshotCatalog | None,
) -> None:
    """Require repository writes to resolve any material pricing reference."""
    if pricing_catalog is None:
        if run.source_type is SourceType.API_EXACT or run.pricing_snapshot_id is not None:
            raise RepositoryConflictError(
                f"planned run {run.run_id!r} requires a PricingSnapshotCatalog"
            )
        return

    try:
        validated_catalog = PricingSnapshotCatalog.model_validate(
            pricing_catalog.model_dump(mode="python")
        )
        validated_catalog.validate_profile_reference(run)
    except ValueError as error:
        raise RepositoryConflictError(
            f"planned run {run.run_id!r} has invalid pricing provenance: {error}"
        ) from error


@runtime_checkable
class Repository(Protocol):
    def create_batch(self, batch: BenchmarkBatch) -> BenchmarkBatch: ...

    def get_batch(self, batch_id: str) -> BenchmarkBatch | None: ...

    def transition_batch(
        self,
        batch_id: str,
        new_status: BatchStatus,
        *,
        at: datetime | None = None,
        invalid_run_count: int | None = None,
        valid_for_scoring_count: int | None = None,
    ) -> BenchmarkBatch: ...

    def create_planned_run(
        self,
        run: PlannedRun,
        *,
        pricing_catalog: PricingSnapshotCatalog | None = None,
    ) -> PlannedRun: ...

    def get_planned_run(self, run_id: str) -> PlannedRun | None: ...

    def get_planned_run_by_identity(
        self,
        batch_id: str,
        model_profile_id: str,
        case_id: str,
        rep_index: int,
    ) -> PlannedRun | None: ...

    def list_planned_runs_for_batch(self, batch_id: str) -> list[PlannedRun]: ...


class SQLiteRepository:
    """SQLite-backed repository with idempotent batch and planned-run creation."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @classmethod
    def from_database(cls, database: str | Path) -> SQLiteRepository:
        apply_migrations(database)
        return cls(connect_sqlite(database))

    @classmethod
    def open_for_verification(cls, database: str | Path) -> SQLiteRepository:
        """Open a read-only repository for checksum verification without mutating schema."""
        require_current_migrations(database)
        return cls(connect_sqlite_readonly(database))

    def create_batch(self, batch: BenchmarkBatch) -> BenchmarkBatch:
        batch = _revalidate_batch(batch)
        existing = self.get_batch(batch.batch_id)
        if existing is not None:
            if _batches_equal(existing, batch):
                return existing
            raise RepositoryConflictError(
                f"batch_id {batch.batch_id!r} already exists with conflicting data"
            )
        if batch.status is not BatchStatus.PLANNED:
            raise BatchLifecycleError(
                "new batches must be created with status 'planned'; "
                "use transition_batch for lifecycle changes"
            )
        if batch.invalid_run_count != 0 or batch.valid_for_scoring_count != 0:
            raise BatchLifecycleError(
                "new planned batches require invalid_run_count and "
                "valid_for_scoring_count to be 0"
            )
        self._connection.execute(
            """
            INSERT INTO benchmark_batches (
                batch_id,
                batch_purpose,
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
                reproduction_checksum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _batch_to_row(batch),
        )
        self._connection.commit()
        stored = self.get_batch(batch.batch_id)
        if stored is None:
            raise RuntimeError(f"failed to persist batch {batch.batch_id!r}")
        return stored

    def get_batch(self, batch_id: str) -> BenchmarkBatch | None:
        row = self._connection.execute(
            "SELECT * FROM benchmark_batches WHERE batch_id = ?",
            (batch_id,),
        ).fetchone()
        return None if row is None else _row_to_batch(row)

    def transition_batch(
        self,
        batch_id: str,
        new_status: BatchStatus,
        *,
        at: datetime | None = None,
        invalid_run_count: int | None = None,
        valid_for_scoring_count: int | None = None,
    ) -> BenchmarkBatch:
        batch = self.get_batch(batch_id)
        if batch is None:
            raise BatchLifecycleError(f"batch_id {batch_id!r} does not exist")
        updated = apply_batch_transition(
            batch,
            new_status,
            planned_runs=self.list_planned_runs_for_batch(batch_id),
            at=at,
            invalid_run_count=invalid_run_count,
            valid_for_scoring_count=valid_for_scoring_count,
        )
        cursor = self._connection.execute(
            """
            UPDATE benchmark_batches
            SET status = ?,
                started_at = ?,
                completed_at = ?,
                invalid_run_count = ?,
                valid_for_scoring_count = ?,
                reproduction_checksum = ?
            WHERE batch_id = ? AND status = ?
            """,
            (
                updated.status.value,
                _datetime_to_iso(updated.started_at),
                _datetime_to_iso(updated.completed_at),
                updated.invalid_run_count,
                updated.valid_for_scoring_count,
                updated.reproduction_checksum,
                batch_id,
                batch.status.value,
            ),
        )
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise BatchLifecycleError(
                f"batch {batch_id!r} status changed concurrently; transition was not applied"
            )
        self._connection.commit()
        stored = self.get_batch(batch_id)
        if stored is None:
            raise RuntimeError(f"failed to persist batch transition for {batch_id!r}")
        return stored

    def create_planned_run(
        self,
        run: PlannedRun,
        *,
        pricing_catalog: PricingSnapshotCatalog | None = None,
    ) -> PlannedRun:
        run = _revalidate_planned_run(run)
        if not run.profile_provenance_complete:
            raise RepositoryConflictError(
                "new planned runs require complete profile provenance"
            )
        _validate_planned_run_pricing(run, pricing_catalog)
        batch = self.get_batch(run.batch_id)
        if batch is None:
            raise RepositoryConflictError(
                f"batch_id {run.batch_id!r} does not exist; create the batch first"
            )
        if batch.status is not BatchStatus.PLANNED:
            raise RepositoryConflictError(
                f"planned runs can only be created while batch {run.batch_id!r} "
                f"status is 'planned' (found {batch.status.value!r})"
            )
        _validate_planned_run_batch_provenance(batch, run)

        existing_by_identity = self.get_planned_run_by_identity(
            run.batch_id,
            run.model_profile_id,
            run.case_id,
            run.rep_index,
        )
        if existing_by_identity is not None:
            if _planned_runs_equal(existing_by_identity, run):
                return existing_by_identity
            raise RepositoryConflictError(
                "planned run identity already exists with conflicting data: "
                f"batch_id={run.batch_id!r}, model_profile_id={run.model_profile_id!r}, "
                f"case_id={run.case_id!r}, rep_index={run.rep_index}"
            )

        existing_by_run_id = self.get_planned_run(run.run_id)
        if existing_by_run_id is not None:
            raise RepositoryConflictError(
                f"run_id {run.run_id!r} already exists for a different planned-run identity"
            )

        try:
            cursor = self._connection.execute(
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
                    local_model_identity_json,
                    routed_provider_identity_json,
                    profile_provenance_complete,
                    pricing_snapshot_id,
                    model_parameters_json
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE EXISTS (
                    SELECT 1 FROM benchmark_batches
                    WHERE batch_id = ? AND status = ?
                )
                """,
                (*_planned_run_to_row(run), run.batch_id, BatchStatus.PLANNED.value),
            )
            if cursor.rowcount != 1:
                self._connection.rollback()
                raise RepositoryConflictError(
                    f"planned runs can only be created while batch {run.batch_id!r} "
                    "status is 'planned'"
                )
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise RepositoryConflictError(
                f"failed to create planned run {run.run_id!r}: {error}"
            ) from error

        stored = self.get_planned_run(run.run_id)
        if stored is None:
            raise RuntimeError(f"failed to persist planned run {run.run_id!r}")
        return stored

    def get_planned_run(self, run_id: str) -> PlannedRun | None:
        row = self._connection.execute(
            "SELECT * FROM planned_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        return None if row is None else _row_to_planned_run(row)

    def get_planned_run_by_identity(
        self,
        batch_id: str,
        model_profile_id: str,
        case_id: str,
        rep_index: int,
    ) -> PlannedRun | None:
        row = self._connection.execute(
            """
            SELECT * FROM planned_runs
            WHERE batch_id = ? AND model_profile_id = ? AND case_id = ? AND rep_index = ?
            """,
            (batch_id, model_profile_id, case_id, rep_index),
        ).fetchone()
        return None if row is None else _row_to_planned_run(row)

    def list_planned_runs_for_batch(self, batch_id: str) -> list[PlannedRun]:
        rows = self._connection.execute(
            """
            SELECT * FROM planned_runs
            WHERE batch_id = ?
            ORDER BY rep_index, model_profile_id, case_id
            """,
            (batch_id,),
        ).fetchall()
        return [_row_to_planned_run(row) for row in rows]

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> SQLiteRepository:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
