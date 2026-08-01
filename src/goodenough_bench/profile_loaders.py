"""Strict loaders for versioned model profiles and dated pricing snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Sequence, TypeVar

from pydantic import Field, ValidationError, field_validator, model_validator

from goodenough_bench.boundaries import (
    BoundaryModel,
    Identifier,
    ModelParameters,
    ModelProfileReference,
    PlannedRun,
    RoutedProviderIdentity,
    SemVer,
    SourceType,
)
from goodenough_bench.exceptions import ConfigLoadError

_MODEL_PROFILE_DIR = "model_profiles"
_PRICING_SNAPSHOT_DIR = "pricing_snapshots"
_MVP_CURRENCY = "USD"

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
    routed_provider_identity: RoutedProviderIdentity | None
    provenance: PricingProvenance
    inferred: bool

    @field_validator("currency")
    @classmethod
    def currency_is_mvp_usd(cls, value: str) -> str:
        if value != _MVP_CURRENCY:
            raise ValueError(f"currency must be {_MVP_CURRENCY!r} for MVP pricing snapshots")
        return value

    @model_validator(mode="after")
    def routed_pricing_has_route_identity(self) -> PricingSnapshot:
        if self.provider == "openrouter" and self.routed_provider_identity is None:
            raise ValueError("openrouter pricing snapshots require routed_provider_identity")
        if self.provider != "openrouter" and self.routed_provider_identity is not None:
            raise ValueError(
                "only openrouter pricing snapshots may define routed_provider_identity"
            )
        return self


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

    def validate_profile_reference(
        self,
        profile: ModelProfileReference | PlannedRun,
    ) -> None:
        """Resolve and validate one profile's pricing reference against this catalog."""
        snapshot_id = profile.pricing_snapshot_id
        if profile.source_type is SourceType.LOCAL_EXACT:
            if snapshot_id is not None:
                raise ValueError(
                    "local_exact profile "
                    f"{profile.model_profile_id!r} must not reference a pricing snapshot"
                )
            return

        if profile.source_type is SourceType.API_EXACT and snapshot_id is None:
            raise ValueError(
                "api_exact profile "
                f"{profile.model_profile_id!r} requires pricing_snapshot_id"
            )

        if snapshot_id is None:
            return

        snapshot = self.snapshot_by_id().get(snapshot_id)
        if snapshot is None:
            raise ValueError(
                "model profile "
                f"{profile.model_profile_id!r} references unknown pricing snapshot "
                f"{snapshot_id!r}"
            )
        if snapshot.provider != profile.provider:
            raise ValueError(
                "model profile "
                f"{profile.model_profile_id!r} provider {profile.provider!r} does not match "
                f"pricing snapshot {snapshot_id!r} provider {snapshot.provider!r}"
            )
        if snapshot.model_identifier != profile.exact_model_identifier:
            raise ValueError(
                "model profile "
                f"{profile.model_profile_id!r} exact_model_identifier "
                f"{profile.exact_model_identifier!r} does not match pricing snapshot "
                f"{snapshot_id!r} model_identifier {snapshot.model_identifier!r}"
            )
        if snapshot.routed_provider_identity != profile.routed_provider_identity:
            raise ValueError(
                "model profile "
                f"{profile.model_profile_id!r} routed_provider_identity does not match "
                f"pricing snapshot {snapshot_id!r}"
            )


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


def default_config_root() -> Path:
    """Return config packaged beside the imported distribution."""
    return Path(__file__).resolve().parent / "config"


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
    for profile in catalog.ordered_profiles:
        try:
            pricing_catalog.validate_profile_reference(profile)
        except ValueError as exc:
            raise ConfigLoadError(str(exc)) from exc

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
