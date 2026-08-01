from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError

from goodenough_bench.boundaries import (
    ExecutionEnvironment,
    IdentityConfidence,
    ProviderSurface,
    SourceType,
)
from goodenough_bench.exceptions import ConfigLoadError
from goodenough_bench.profile_loaders import (
    ModelProfileCatalog,
    PricingSnapshotCatalog,
    default_config_root,
    load_model_profiles,
    load_pricing_snapshots,
    synthetic_model_parameters,
)


REPO_CONFIG = default_config_root()


class ProfileLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.temp_config = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _copy_repo_config(self) -> None:
        shutil.copytree(REPO_CONFIG / "model_profiles", self.temp_config / "model_profiles")
        shutil.copytree(REPO_CONFIG / "pricing_snapshots", self.temp_config / "pricing_snapshots")

    def _write_json(self, relative_path: str, payload: object) -> Path:
        path = self.temp_config / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def test_load_repository_pricing_snapshots(self) -> None:
        catalog = load_pricing_snapshots(config_root=REPO_CONFIG)

        self.assertEqual(len(catalog.snapshots), 4)
        self.assertEqual(
            [snapshot.pricing_snapshot_id for snapshot in catalog.ordered_snapshots],
            sorted(snapshot.pricing_snapshot_id for snapshot in catalog.snapshots),
        )
        deepseek = catalog.snapshot_by_id()["synthetic-deepseek-v4-flash-2026-01-01"]
        self.assertEqual(deepseek.provider, "deepseek")
        self.assertEqual(deepseek.input_price, Decimal("0.140000"))
        self.assertTrue(deepseek.inferred)
        self.assertIn("Synthetic placeholder", deepseek.provenance.notes)

    def test_load_repository_model_profiles_with_snapshot_validation(self) -> None:
        catalog = load_model_profiles(config_root=REPO_CONFIG)

        self.assertEqual(len(catalog.profiles), 5)
        self.assertEqual(
            [profile.model_profile_id for profile in catalog.ordered_profiles],
            sorted(profile.model_profile_id for profile in catalog.profiles),
        )
        routed = catalog.profile_by_id()["synthetic-openrouter-deepseek-v4-flash-api"]
        self.assertEqual(routed.provider_surface, ProviderSurface.OPENROUTER_API)
        self.assertEqual(
            routed.pricing_snapshot_id,
            "synthetic-openrouter-deepseek-v4-flash-2026-01-01",
        )

    def test_deterministic_reload_produces_identical_catalog_checksum(self) -> None:
        first = load_model_profiles(config_root=REPO_CONFIG)
        second = load_model_profiles(config_root=REPO_CONFIG)

        self.assertEqual(first.catalog_checksum(), second.catalog_checksum())
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertNotEqual(first.catalog_checksum(), "")

    def test_pricing_catalog_canonical_json_is_sorted(self) -> None:
        catalog = load_pricing_snapshots(config_root=REPO_CONFIG)
        payload = json.loads(catalog.canonical_json())

        self.assertEqual(
            [item["pricing_snapshot_id"] for item in payload],
            sorted(item["pricing_snapshot_id"] for item in payload),
        )

    def test_references_returns_model_profile_reference_objects(self) -> None:
        catalog = load_model_profiles(config_root=REPO_CONFIG)
        references = catalog.references()

        self.assertEqual(len(references), len(catalog.profiles))
        local = next(
            ref for ref in references if ref.model_profile_id == "synthetic-qwen35-9b-ollama-q4km"
        )
        self.assertEqual(local.source_type, SourceType.LOCAL_EXACT)
        self.assertIsNone(local.pricing_snapshot_id)

    def test_invalid_json_raises_config_load_error(self) -> None:
        self._copy_repo_config()
        bad_path = self.temp_config / "pricing_snapshots" / "broken.json"
        bad_path.write_text("{not json", encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "invalid JSON"):
            load_pricing_snapshots(config_root=self.temp_config)

    def test_negative_price_rejected(self) -> None:
        self._copy_repo_config()
        self._write_json(
            "pricing_snapshots/negative-rate.json",
            {
                "pricing_snapshot_id": "negative-rate",
                "effective_date": "2026-01-01",
                "provider": "openai",
                "model_identifier": "gpt-negative",
                "input_price": "-1.0",
                "output_price": "0.10",
                "currency": "USD",
                "price_unit": "per_million_tokens",
                "provenance": {
                    "source_label": "test",
                    "source_url": None,
                    "captured_at": "2026-01-01",
                    "notes": "",
                },
                "inferred": True,
            },
        )

        with self.assertRaises(ConfigLoadError):
            load_pricing_snapshots(config_root=self.temp_config)

    def test_duplicate_snapshot_ids_rejected(self) -> None:
        self._copy_repo_config()
        duplicate = REPO_CONFIG / "pricing_snapshots" / "synthetic-deepseek-v4-flash-2026-01-01.json"
        shutil.copyfile(
            duplicate,
            self.temp_config / "pricing_snapshots" / "duplicate-deepseek.json",
        )

        with self.assertRaisesRegex(ConfigLoadError, "unique pricing_snapshot_id"):
            load_pricing_snapshots(config_root=self.temp_config)

    def test_duplicate_profile_ids_rejected(self) -> None:
        self._copy_repo_config()
        duplicate = REPO_CONFIG / "model_profiles" / "synthetic-qwen35-9b-ollama-q4km.json"
        shutil.copyfile(
            duplicate,
            self.temp_config / "model_profiles" / "duplicate-qwen.json",
        )

        with self.assertRaisesRegex(ConfigLoadError, "unique model_profile_id"):
            load_model_profiles(config_root=self.temp_config)

    def test_missing_pricing_snapshot_reference_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-deepseek-v4-flash-api.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["pricing_snapshot_id"] = "missing-snapshot"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "unknown pricing snapshot"):
            load_model_profiles(config_root=self.temp_config)

    def test_local_profile_with_pricing_snapshot_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-qwen35-9b-ollama-q4km.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["pricing_snapshot_id"] = "synthetic-deepseek-v4-flash-2026-01-01"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "must not reference a pricing snapshot"):
            load_model_profiles(config_root=self.temp_config)

    def test_api_exact_without_pricing_snapshot_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-deepseek-v4-flash-api.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["pricing_snapshot_id"] = None
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "requires pricing_snapshot_id"):
            load_model_profiles(config_root=self.temp_config)

    def test_provider_snapshot_mismatch_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-deepseek-v4-flash-api.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["provider"] = "openai"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "provider"):
            load_model_profiles(config_root=self.temp_config)

    def test_model_identifier_snapshot_mismatch_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-deepseek-v4-flash-api.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["exact_model_identifier"] = "deepseek-v4-flash-wrong"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "exact_model_identifier"):
            load_model_profiles(config_root=self.temp_config)

    def test_surface_source_conflict_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-deepseek-v4-flash-api.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["provider_surface"] = "ollama_local"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "incompatible provider_surface"):
            load_model_profiles(config_root=self.temp_config)

    def test_each_api_surface_requires_its_provider(self) -> None:
        self._copy_repo_config()
        profile_path = (
            self.temp_config / "model_profiles" / "synthetic-openrouter-deepseek-v4-flash-api.json"
        )
        original = json.loads(profile_path.read_text(encoding="utf-8"))

        for surface in (
            "openai_responses_api",
            "google_gemini_api",
            "deepseek_api",
            "openrouter_api",
        ):
            with self.subTest(provider_surface=surface):
                profile = original.copy()
                profile["provider_surface"] = surface
                profile["provider"] = "incorrect-provider"
                profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

                with self.assertRaisesRegex(ConfigLoadError, "requires provider"):
                    load_model_profiles(config_root=self.temp_config)

    def test_ollama_local_surface_requires_ollama_provider(self) -> None:
        self._copy_repo_config()
        profile_path = (
            self.temp_config / "model_profiles" / "synthetic-qwen35-9b-ollama-q4km.json"
        )
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["provider"] = "openai"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "requires provider 'ollama'"):
            load_model_profiles(config_root=self.temp_config)

    def test_reversed_direct_and_routed_provider_pairing_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = (
            self.temp_config / "model_profiles" / "synthetic-openrouter-deepseek-v4-flash-api.json"
        )
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["provider_surface"] = "deepseek_api"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ConfigLoadError, "requires provider 'deepseek'"):
            load_model_profiles(config_root=self.temp_config)

    def test_malformed_profile_version_rejected(self) -> None:
        self._copy_repo_config()
        profile_path = self.temp_config / "model_profiles" / "synthetic-qwen35-9b-ollama-q4km.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["profile_version"] = "not-a-version"
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        with self.assertRaises(ConfigLoadError):
            load_model_profiles(config_root=self.temp_config)

    def test_malformed_effective_date_rejected(self) -> None:
        self._copy_repo_config()
        snapshot_path = (
            self.temp_config / "pricing_snapshots" / "synthetic-deepseek-v4-flash-2026-01-01.json"
        )
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["effective_date"] = "31-01-2026"
        snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

        with self.assertRaises(ConfigLoadError):
            load_pricing_snapshots(config_root=self.temp_config)

    def test_cloud_identity_fields_rejected_on_local_profile(self) -> None:
        payload = {
            "profile_version": "v0.1.0",
            "model_profile_id": "bad-local-cloud-mix",
            "exact_model_identifier": "qwen3.5:9b",
            "displayed_model_name": "Bad Mix",
            "provider": "ollama",
            "provider_surface": "ollama_local",
            "provider_host": "localhost",
            "source_type": "local_exact",
            "collection_method": "test/0.1.0",
            "model_identity_confidence": "high",
            "execution_environment": "cloud",
            "runtime": "ollama 0.32.5",
            "quantization": "Q4_K_M",
            "hardware_profile_id": "synthetic-theimp-2026-01-01",
            "pricing_snapshot_id": None,
            "model_parameters": synthetic_model_parameters().model_dump(),
            "superseded_by": None,
            "notes": "",
        }
        self._write_json("model_profiles/bad-local-cloud-mix.json", payload)
        shutil.copytree(REPO_CONFIG / "pricing_snapshots", self.temp_config / "pricing_snapshots")

        with self.assertRaises(ConfigLoadError):
            load_model_profiles(config_root=self.temp_config)

    def test_catalog_models_reject_duplicate_ids_directly(self) -> None:
        snapshot = load_pricing_snapshots(config_root=REPO_CONFIG).snapshots[0]
        with self.assertRaises(ValidationError):
            PricingSnapshotCatalog(snapshots=[snapshot, snapshot])

        profile = load_model_profiles(config_root=REPO_CONFIG).profiles[0]
        with self.assertRaises(ValidationError):
            ModelProfileCatalog(profiles=[profile, profile])

    def test_missing_directory_raises_config_load_error(self) -> None:
        with self.assertRaisesRegex(ConfigLoadError, "missing pricing snapshot directory"):
            load_pricing_snapshots(config_root=self.temp_config)

    def test_load_with_explicit_pricing_catalog(self) -> None:
        pricing = load_pricing_snapshots(config_root=REPO_CONFIG)
        profiles = load_model_profiles(config_root=REPO_CONFIG, pricing_catalog=pricing)

        self.assertEqual(len(profiles.profiles), 5)
        cloud = profiles.profile_by_id()["synthetic-deepseek-v4-flash-api"]
        self.assertEqual(cloud.execution_environment, ExecutionEnvironment.CLOUD)
        self.assertEqual(cloud.model_identity_confidence, IdentityConfidence.HIGH)


if __name__ == "__main__":
    unittest.main()
