"""Strict loaders for versioned model profiles and dated pricing snapshots."""

from __future__ import annotations

import hashlib
import json
import re
import sysconfig
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Sequence, TypeVar

from pydantic import Field, ValidationError, field_validator, model_validator

from goodenough_bench.boundaries import (
    BoundaryModel,
    ExecutionEnvironment,
    Identifier,
    IdentityConfidence,
    ModelParameters,
    ModelProfileReference,
    ProviderSurface,
    SemVer,
    SourceType,
)
from goodenough_bench.exceptions import ConfigLoadError

_MODEL_PROFILE_DIR = "model_profiles"
_PRICING_SNAPSHOT_DIR = "pricing_snapshots"
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")

T = TypeVar("T", bound=BoundaryModel)


class PriceUnit(str, Enum):
    PER_MILLION_TOKENS = "per_million_tokens"


class PricingProvenance(BoundaryModel):
    """Source metadata for a captured pricing snapshot; not a live price claim."""

    source_label: str = Field(min_length=1)
    source_url: str | None = None
    captured_at: date
    notes: str = ""


class PricingSnapshot(BoundaryModel):
    """Dated provider pricing record for deterministic cost calculations."""

    pricing_snapshot_id: Identifier
    effective_date: date
    provider: Identifier
    model_identifier: str = Field(min_length=1)
    input_price: Decimal = Field(ge=0)
    output_price: Decimal = Field(ge=0)
    currency: str
    price_unit: PriceUnit
    provenance: PricingProvenance
    inferred: bool

    @field_validator("currency")
    @classmethod
    def currency_is_iso4217(cls, value: str) -> str:
        if not _CURRENCY_PATTERN.fullmatch(value):
            raise ValueError("currency must be a three-letter ISO 4217 code")
        return value


class ModelProfileDocument(ModelProfileReference):
    """Versioned model profile loaded from repository-controlled config."""

    profile_version: SemVer
    superseded_by: Identifier | None = None
    notes: str = ""


class PricingSnapshotCatalog(BoundaryModel):
    snapshots: list[PricingSnapshot] = Field(min_length=1)

    @model_validator(mode="after")
    def snapshots_have_unique_ids(self) -> PricingSnapshotCatalog:
        snapshot_ids = [snapshot.pricing_snapshot_id for snapshot in self.snapshots]
        if len(snapshot_ids) != len(set(snapshot_ids)):
            raise ValueError("pricing snapshots must have unique pricing_snapshot_id values")
        return self

    @property
    def ordered_snapshots(self) -> list[PricingSnapshot]:
        return sorted(self.snapshots, key=lambda snapshot: snapshot.pricing_snapshot_id)

    def snapshot_by_id(self) -> dict[str, PricingSnapshot]:
        return {snapshot.pricing_snapshot_id: snapshot for snapshot in self.ordered_snapshots}

    def canonical_json(self) -> str:
        return _canonical_json(self.ordered_snapshots)

    def catalog_checksum(self) -> str:
        return _catalog_checksum(self.ordered_snapshots)


class ModelProfileCatalog(BoundaryModel):
    profiles: list[ModelProfileDocument] = Field(min_length=1)

    @model_validator(mode="after")
    def profiles_have_unique_ids(self) -> ModelProfileCatalog:
        profile_ids = [profile.model_profile_id for profile in self.profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("model profiles must have unique model_profile_id values")
        return self

    @property
    def ordered_profiles(self) -> list[ModelProfileDocument]:
        return sorted(self.profiles, key=lambda profile: profile.model_profile_id)

    def profile_by_id(self) -> dict[str, ModelProfileDocument]:
        return {profile.model_profile_id: profile for profile in self.ordered_profiles}

    def references(self) -> list[ModelProfileReference]:
        return [
            ModelProfileReference.model_validate(
                profile.model_dump(
                    include=set(ModelProfileReference.model_fields.keys()),
                )
            )
            for profile in self.ordered_profiles
        ]

    def canonical_json(self) -> str:
        return _canonical_json(self.ordered_profiles)

    def catalog_checksum(self) -> str:
        return _catalog_checksum(self.ordered_profiles)


_API_EXACT_SURFACES = frozenset(
    {
        ProviderSurface.OPENAI_RESPONSES_API,
        ProviderSurface.GOOGLE_GEMINI_API,
        ProviderSurface.DEEPSEEK_API,
        ProviderSurface.OPENROUTER_API,
    }
)

_PROVIDER_SURFACE_BY_SOURCE: dict[SourceType, frozenset[ProviderSurface]] = {
    SourceType.LOCAL_EXACT: frozenset({ProviderSurface.OLLAMA_LOCAL}),
    SourceType.API_EXACT: _API_EXACT_SURFACES,
    SourceType.CLI_EXACT: frozenset({ProviderSurface.OFFICIAL_CLI}),
    SourceType.WEB_DECLARED: frozenset({ProviderSurface.CONSUMER_WEB}),
    SourceType.WEB_OPAQUE: frozenset({ProviderSurface.CONSUMER_WEB}),
    SourceType.MANUAL_IMPORT: frozenset(
        {ProviderSurface.MANUAL_IMPORT, ProviderSurface.AUTOGEMINI_IMPORT}
    ),
}


def default_config_root() -> Path:
    """Return the repository or installed-package config root."""
    package_dir = Path(__file__).resolve().parent
    repo_config = package_dir.parent.parent / "config"
    if (repo_config / _MODEL_PROFILE_DIR).is_dir():
        return repo_config

    site_packages = Path(sysconfig.get_path("purelib"))
    install_data = Path(sysconfig.get_path("data"))
    installed_candidates = (
        site_packages.parent / "goodenough_bench" / "config",
        site_packages / "goodenough_bench" / "config",
        install_data / "goodenough_bench" / "config",
    )
    for candidate in installed_candidates:
        if (candidate / _MODEL_PROFILE_DIR).is_dir():
            return candidate

    for candidate in site_packages.glob(
        "goodenough_bench-*.data/data/goodenough_bench/config"
    ):
        if (candidate / _MODEL_PROFILE_DIR).is_dir():
            return candidate

    return repo_config


def load_pricing_snapshots(
    config_root: Path | None = None,
) -> PricingSnapshotCatalog:
    """Load and validate all pricing snapshots under ``config/pricing_snapshots``."""
    root = config_root if config_root is not None else default_config_root()
    directory = root / _PRICING_SNAPSHOT_DIR
    snapshots = _load_documents(directory, PricingSnapshot, label="pricing snapshot")
    try:
        return PricingSnapshotCatalog(snapshots=snapshots)
    except ValidationError as exc:
        raise ConfigLoadError(f"invalid pricing snapshot catalog in {directory}: {exc}") from exc


def load_model_profiles(
    config_root: Path | None = None,
    *,
    pricing_catalog: PricingSnapshotCatalog | None = None,
) -> ModelProfileCatalog:
    """Load model profiles and validate pricing-snapshot references when provided."""
    root = config_root if config_root is not None else default_config_root()
    directory = root / _MODEL_PROFILE_DIR
    profiles = _load_documents(directory, ModelProfileDocument, label="model profile")
    try:
        catalog = ModelProfileCatalog(profiles=profiles)
    except ValidationError as exc:
        raise ConfigLoadError(f"invalid model profile catalog in {directory}: {exc}") from exc
    pricing = (
        pricing_catalog
        if pricing_catalog is not None
        else load_pricing_snapshots(config_root=root)
    )
    _validate_profile_pricing_references(catalog, pricing)
    return catalog


def _load_documents(
    directory: Path,
    model: type[T],
    *,
    label: str,
) -> list[T]:
    if not directory.is_dir():
        raise ConfigLoadError(f"missing {label} directory: {directory}")
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ConfigLoadError(f"no {label} documents found in {directory}")

    documents: list[T] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigLoadError(f"invalid JSON in {path}: {exc}") from exc
        try:
            documents.append(model.model_validate(payload))
        except Exception as exc:
            raise ConfigLoadError(f"invalid {label} document {path}: {exc}") from exc
    return documents


def _validate_profile_pricing_references(
    catalog: ModelProfileCatalog,
    pricing_catalog: PricingSnapshotCatalog,
) -> None:
    snapshots = pricing_catalog.snapshot_by_id()
    for profile in catalog.ordered_profiles:
        _validate_profile_surface_rules(profile)
        snapshot_id = profile.pricing_snapshot_id
        if profile.source_type is SourceType.LOCAL_EXACT:
            if snapshot_id is not None:
                raise ConfigLoadError(
                    "local_exact profile "
                    f"{profile.model_profile_id!r} must not reference a pricing snapshot"
                )
            continue

        if profile.source_type is SourceType.API_EXACT and snapshot_id is None:
            raise ConfigLoadError(
                "api_exact profile "
                f"{profile.model_profile_id!r} requires pricing_snapshot_id"
            )

        if snapshot_id is None:
            continue

        snapshot = snapshots.get(snapshot_id)
        if snapshot is None:
            raise ConfigLoadError(
                "model profile "
                f"{profile.model_profile_id!r} references unknown pricing snapshot "
                f"{snapshot_id!r}"
            )
        if snapshot.provider != profile.provider:
            raise ConfigLoadError(
                "model profile "
                f"{profile.model_profile_id!r} provider {profile.provider!r} does not match "
                f"pricing snapshot {snapshot_id!r} provider {snapshot.provider!r}"
            )
        if snapshot.model_identifier != profile.exact_model_identifier:
            raise ConfigLoadError(
                "model profile "
                f"{profile.model_profile_id!r} exact_model_identifier "
                f"{profile.exact_model_identifier!r} does not match pricing snapshot "
                f"{snapshot_id!r} model_identifier {snapshot.model_identifier!r}"
            )


def _validate_profile_surface_rules(profile: ModelProfileDocument) -> None:
    allowed_surfaces = _PROVIDER_SURFACE_BY_SOURCE.get(profile.source_type)
    if allowed_surfaces is None:
        raise ConfigLoadError(
            f"unsupported source_type {profile.source_type.value!r} "
            f"for profile {profile.model_profile_id!r}"
        )
    if profile.provider_surface not in allowed_surfaces:
        raise ConfigLoadError(
            f"profile {profile.model_profile_id!r} combines source_type "
            f"{profile.source_type.value!r} with incompatible provider_surface "
            f"{profile.provider_surface.value!r}"
        )

    if (
        profile.provider_surface is ProviderSurface.OPENROUTER_API
        and profile.provider == "deepseek"
    ):
        raise ConfigLoadError(
            "profile "
            f"{profile.model_profile_id!r} must not use provider 'deepseek' with "
            "openrouter_api; routed and direct DeepSeek surfaces must remain distinct"
        )

    if profile.source_type is SourceType.API_EXACT:
        if profile.execution_environment is not ExecutionEnvironment.CLOUD:
            raise ConfigLoadError(
                f"api_exact profile {profile.model_profile_id!r} must use cloud environment"
            )
    if profile.source_type is SourceType.LOCAL_EXACT:
        if profile.execution_environment is not ExecutionEnvironment.LOCAL:
            raise ConfigLoadError(
                f"local_exact profile {profile.model_profile_id!r} must use local environment"
            )


def _canonical_json(documents: Sequence[BoundaryModel]) -> str:
    payload = [_json_ready(document.model_dump(mode="json")) for document in documents]
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def _catalog_checksum(documents: Sequence[BoundaryModel]) -> str:
    return hashlib.sha256(_canonical_json(documents).encode("utf-8")).hexdigest()


def synthetic_model_parameters() -> ModelParameters:
    """Shared deterministic parameters for repository synthetic profile fixtures."""
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
