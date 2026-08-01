from __future__ import annotations

import hashlib
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from goodenough_bench.artifact_store import (
    FilesystemArtifactStore,
    artifact_ref_for_body,
    parse_verified_artifact,
    sha256_hex,
    storage_ref_for_run,
)
from goodenough_bench.exceptions import ArtifactConflictError, ArtifactCorruptionError


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "raw"
        self.store = FilesystemArtifactStore(self.root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_successful_write_and_verify(self) -> None:
        body = b'{"invoice_id":"INV-001"}'
        ref = self.store.write_immutable(run_id="run-001", body=body)

        self.assertTrue(self.store.verify(ref))
        self.assertEqual(self.store.read_bytes(ref), body)
        self.assertTrue((self.root / ref.storage_ref).is_file())

    def test_deterministic_references_and_checksums(self) -> None:
        body = b"provider-bytes-42"
        expected_checksum = hashlib.sha256(body).hexdigest()
        expected_ref = artifact_ref_for_body("run-002", body)

        first = self.store.write_immutable(run_id="run-002", body=body)
        second = self.store.write_immutable(run_id="run-002", body=body)

        self.assertEqual(first, second)
        self.assertEqual(first.checksum, expected_checksum)
        self.assertEqual(first.storage_ref, storage_ref_for_run("run-002"))
        self.assertEqual(first, expected_ref)
        self.assertEqual(sha256_hex(body), expected_checksum)

    def test_conflicting_rewrite_rejection(self) -> None:
        self.store.write_immutable(run_id="run-003", body=b"first-body")
        with self.assertRaisesRegex(ArtifactConflictError, "refusing rewrite"):
            self.store.write_immutable(run_id="run-003", body=b"second-body")

    def test_corruption_detection(self) -> None:
        ref = self.store.write_immutable(run_id="run-004", body=b"immutable")
        path = self.store.resolve_path(ref)
        path.write_bytes(b"tampered")

        self.assertFalse(self.store.verify(ref))
        with self.assertRaisesRegex(ArtifactCorruptionError, "failed verification"):
            self.store.read_bytes(ref)

    def test_write_before_parse_integration(self) -> None:
        body = b'{"status":"ok"}'
        ref = self.store.write_immutable(run_id="run-005", body=body)

        def parser(raw: bytes) -> dict[str, str]:
            self.assertEqual(raw, body)
            return {"status": "ok"}

        record = parse_verified_artifact(self.store, ref, parser)

        self.assertEqual(record, {"status": "ok"})

    def test_parse_gate_rejects_unverified_artifact(self) -> None:
        ref = artifact_ref_for_body("run-006", b"missing")
        with self.assertRaisesRegex(ArtifactCorruptionError, "cannot parse"):
            parse_verified_artifact(self.store, ref, lambda body: body)

    def test_parse_gate_rejects_corrupted_artifact(self) -> None:
        ref = self.store.write_immutable(run_id="run-007", body=b"original")
        self.store.resolve_path(ref).write_bytes(b"corrupted")

        with self.assertRaisesRegex(ArtifactCorruptionError, "cannot parse"):
            parse_verified_artifact(self.store, ref, lambda body: body)

    def test_rejects_noncanonical_storage_reference(self) -> None:
        ref = artifact_ref_for_body("run-008", b"body").model_copy(
            update={"storage_ref": "../outside"}
        )
        self.assertFalse(self.store.verify(ref))
        with self.assertRaisesRegex(ArtifactCorruptionError, "unexpected storage reference"):
            self.store.resolve_path(ref)

    def test_concurrent_conflicting_writes_preserve_one_body(self) -> None:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(self.store.write_immutable, run_id="run-009", body=body)
                for body in (b"first", b"second")
            ]
        results = []
        errors = []
        for future in futures:
            try:
                results.append(future.result())
            except ArtifactConflictError as error:
                errors.append(error)

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertTrue(self.store.verify(results[0]))
        self.assertIn(self.store.read_bytes(results[0]), {b"first", b"second"})


if __name__ == "__main__":
    unittest.main()
