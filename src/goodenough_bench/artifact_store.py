"""Immutable filesystem artifact store for provider response bytes."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Callable, Protocol, TypeVar, runtime_checkable

from goodenough_bench.boundaries import (
    ArtifactRef,
    NonEmptyStr,
    Sha256,
)
from goodenough_bench.exceptions import ArtifactConflictError, ArtifactCorruptionError

_DEFAULT_MEDIA_TYPE = "application/octet-stream"
_RUN_SEGMENT = "by-run"
_RAW_FILENAME = "raw.bin"
ParseResult = TypeVar("ParseResult")


def sha256_hex(body: bytes) -> Sha256:
    """Return the SHA-256 hex digest for immutable artifact checksums."""
    return hashlib.sha256(body).hexdigest()


def storage_ref_for_run(run_id: str) -> NonEmptyStr:
    """Deterministic opaque storage reference for a run's raw provider bytes."""
    return f"{_RUN_SEGMENT}/{run_id}/{_RAW_FILENAME}"


def artifact_ref_for_body(run_id: str, body: bytes, media_type: str = _DEFAULT_MEDIA_TYPE) -> ArtifactRef:
    """Build a deterministic artifact reference from run identity and body bytes."""
    return ArtifactRef(
        run_id=run_id,
        storage_ref=storage_ref_for_run(run_id),
        checksum=sha256_hex(body),
        byte_length=len(body),
        media_type=media_type,
    )


@runtime_checkable
class ArtifactStore(Protocol):
    def write_immutable(
        self,
        *,
        run_id: str,
        body: bytes,
        media_type: str = _DEFAULT_MEDIA_TYPE,
    ) -> ArtifactRef: ...

    def verify(self, ref: ArtifactRef) -> bool: ...

    def read_bytes(self, ref: ArtifactRef) -> bytes: ...


class FilesystemArtifactStore:
    """Write-once filesystem store keyed by run_id with content checksum verification."""

    def __init__(self, root: Path) -> None:
        self._root = root

    @classmethod
    def from_default_root(cls, root: Path | None = None) -> FilesystemArtifactStore:
        return cls(root if root is not None else Path("artifacts/raw"))

    def resolve_path(self, ref: ArtifactRef) -> Path:
        """Resolve an opaque storage reference to an absolute filesystem path."""
        expected_ref = storage_ref_for_run(ref.run_id)
        if ref.storage_ref != expected_ref:
            raise ArtifactCorruptionError(
                f"artifact for run_id {ref.run_id!r} has an unexpected storage reference "
                f"{ref.storage_ref!r}"
            )
        root = self._root.resolve()
        path = (root / ref.storage_ref).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ArtifactCorruptionError(
                f"artifact for run_id {ref.run_id!r} escapes the configured artifact root"
            ) from error
        return path

    def write_immutable(
        self,
        *,
        run_id: str,
        body: bytes,
        media_type: str = _DEFAULT_MEDIA_TYPE,
    ) -> ArtifactRef:
        expected = artifact_ref_for_body(run_id, body, media_type=media_type)
        target = self.resolve_path(expected)

        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=target.parent, prefix=".raw-", suffix=".tmp", delete=False
            ) as temporary:
                temporary.write(body)
                temporary.flush()
                os.fsync(temporary.fileno())
                tmp_path = Path(temporary.name)
            try:
                os.link(tmp_path, target)
            except FileExistsError:
                existing_body = target.read_bytes()
                existing_checksum = sha256_hex(existing_body)
                if existing_checksum != expected.checksum:
                    raise ArtifactConflictError(
                        f"run_id {run_id!r} already has immutable raw bytes with checksum "
                        f"{existing_checksum}; refusing rewrite with checksum {expected.checksum}"
                    )
                return artifact_ref_for_body(run_id, existing_body, media_type=media_type)
            return expected
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def verify(self, ref: ArtifactRef) -> bool:
        try:
            path = self.resolve_path(ref)
        except ArtifactCorruptionError:
            return False
        if not path.is_file():
            return False
        body = path.read_bytes()
        if len(body) != ref.byte_length:
            return False
        return sha256_hex(body) == ref.checksum

    def read_bytes(self, ref: ArtifactRef) -> bytes:
        """Read stored bytes after verification; raises on missing or corrupt artifacts."""
        if not self.verify(ref):
            raise ArtifactCorruptionError(
                f"artifact for run_id {ref.run_id!r} at {ref.storage_ref!r} failed verification"
            )
        return self.resolve_path(ref).read_bytes()


def parse_verified_artifact(
    store: ArtifactStore,
    ref: ArtifactRef,
    parser: Callable[[bytes], ParseResult],
) -> ParseResult:
    """Verify and read raw bytes before invoking a parser."""
    try:
        body = store.read_bytes(ref)
    except ArtifactCorruptionError as error:
        raise ArtifactCorruptionError(
            f"cannot parse run_id {ref.run_id!r}: raw artifact failed verification"
        ) from error
    return parser(body)
