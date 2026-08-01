"""Strongly typed boundaries for the benchmark lifecycle.

These models describe data exchanged between planning, collection, artifact,
parsing, and scoring components. They do not implement those components.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

if TYPE_CHECKING:
    from goodenough_bench.profile_loaders import PricingSnapshotCatalog


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Identifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
    ),
]
Sha256 = Annotated[
    str,
    StringConstraints(to_lower=True, pattern=r"^[0-9a-f]{64}$"),
]
GitCommit = Annotated[
    str,
    StringConstraints(to_lower=True, pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"),
]
SemVer = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?:[A-Za-z0-9][A-Za-z0-9.-]*-)?v?\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$"
    ),
]


class ProviderSurface(str, Enum):
    """Approved initial access surfaces; distinct routes remain distinct values."""

    OLLAMA_LOCAL = "ollama_local"
    OPENAI_RESPONSES_API = "openai_responses_api"
    GOOGLE_GEMINI_API = "google_gemini_api"
    DEEPSEEK_API = "deepseek_api"
    OPENROUTER_API = "openrouter_api"
    OFFICIAL_CLI = "official_cli"
    CONSUMER_WEB = "consumer_web"
    MANUAL_IMPORT = "manual_import"
    AUTOGEMINI_IMPORT = "autogemini_import"


class SourceType(str, Enum):
    LOCAL_EXACT = "local_exact"
    API_EXACT = "api_exact"
    CLI_EXACT = "cli_exact"
    WEB_DECLARED = "web_declared"
    WEB_OPAQUE = "web_opaque"
    MANUAL_IMPORT = "manual_import"


class IdentityConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RouteSelectionPolicy(str, Enum):
    """Provider-routing behavior that materially affects model identity."""

    PINNED = "pinned"


class TaskFamily(str, Enum):
    STRUCTURED_EXTRACTION = "structured_extraction"
    CLASSIFICATION_ROUTING = "classification_routing"
    STRUCTURED_NORMALIZATION = "structured_normalization"


class ErrorType(str, Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    PROVIDER_5XX = "provider_5xx"
    INVALID_REQUEST = "invalid_request"
    PARSE_FAILURE = "parse_failure"
    EMPTY_RESPONSE = "empty_response"


class ExecutionEnvironment(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    IMPORT = "import"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CaseStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class BatchStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FROZEN = "frozen"


class BatchPurpose(str, Enum):
    """Explicit batch intent; diagnostic pilot batches are never publishable evidence."""

    DIAGNOSTIC_PILOT = "diagnostic_pilot"
    STABLE_BENCHMARK = "stable_benchmark"


class ReviewOutcome(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class MissingInformationAction(str, Enum):
    RETURN_NULL = "return_null"
    RETURN_UNKNOWN = "return_unknown"
    RETURN_NEEDS_REVIEW = "return_needs_review"


class RedactionStatus(str, Enum):
    PRIVATE = "private"
    REDACTED = "redacted"
    NOT_REQUIRED = "not_required"


class BoundaryModel(BaseModel):
    """Shared strictness for all external and persistence boundaries."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class LocalModelIdentity(BoundaryModel):
    """Immutable local artifact identity plus the configured context window."""

    artifact_digest: Sha256
    artifact_size_bytes: int = Field(ge=1)
    parameter_size: NonEmptyStr
    context_window_tokens: int = Field(ge=1)


class RoutedProviderIdentity(BoundaryModel):
    """Pinned upstream identity for a routed API surface."""

    upstream_provider: Identifier
    upstream_model_identifier: NonEmptyStr
    selection_policy: RouteSelectionPolicy
    allow_fallbacks: bool

    @model_validator(mode="after")
    def pinned_routes_disallow_fallbacks(self) -> RoutedProviderIdentity:
        if self.selection_policy is RouteSelectionPolicy.PINNED and self.allow_fallbacks:
            raise ValueError("pinned routed-provider identity must disallow fallbacks")
        return self


_ALLOWED_SURFACES_BY_SOURCE: dict[SourceType, frozenset[ProviderSurface]] = {
    SourceType.LOCAL_EXACT: frozenset({ProviderSurface.OLLAMA_LOCAL}),
    SourceType.API_EXACT: frozenset(
        {
            ProviderSurface.OPENAI_RESPONSES_API,
            ProviderSurface.GOOGLE_GEMINI_API,
            ProviderSurface.DEEPSEEK_API,
            ProviderSurface.OPENROUTER_API,
        }
    ),
    SourceType.CLI_EXACT: frozenset({ProviderSurface.OFFICIAL_CLI}),
    SourceType.WEB_DECLARED: frozenset({ProviderSurface.CONSUMER_WEB}),
    SourceType.WEB_OPAQUE: frozenset({ProviderSurface.CONSUMER_WEB}),
    SourceType.MANUAL_IMPORT: frozenset(
        {ProviderSurface.MANUAL_IMPORT, ProviderSurface.AUTOGEMINI_IMPORT}
    ),
}

_EXPECTED_CONFIDENCE_BY_SOURCE: dict[SourceType, IdentityConfidence] = {
    SourceType.LOCAL_EXACT: IdentityConfidence.HIGH,
    SourceType.API_EXACT: IdentityConfidence.HIGH,
    SourceType.CLI_EXACT: IdentityConfidence.MEDIUM,
    SourceType.WEB_DECLARED: IdentityConfidence.MEDIUM,
    SourceType.WEB_OPAQUE: IdentityConfidence.LOW,
    SourceType.MANUAL_IMPORT: IdentityConfidence.LOW,
}

_EXPECTED_ENVIRONMENT_BY_SOURCE: dict[SourceType, ExecutionEnvironment] = {
    SourceType.LOCAL_EXACT: ExecutionEnvironment.LOCAL,
    SourceType.API_EXACT: ExecutionEnvironment.CLOUD,
    SourceType.CLI_EXACT: ExecutionEnvironment.CLOUD,
    SourceType.WEB_DECLARED: ExecutionEnvironment.CLOUD,
    SourceType.WEB_OPAQUE: ExecutionEnvironment.CLOUD,
    SourceType.MANUAL_IMPORT: ExecutionEnvironment.IMPORT,
}

_EXPECTED_PROVIDER_BY_SURFACE: dict[ProviderSurface, str] = {
    ProviderSurface.OLLAMA_LOCAL: "ollama",
    ProviderSurface.OPENAI_RESPONSES_API: "openai",
    ProviderSurface.GOOGLE_GEMINI_API: "google",
    ProviderSurface.DEEPSEEK_API: "deepseek",
    ProviderSurface.OPENROUTER_API: "openrouter",
}

_EXPECTED_HOST_BY_API_SURFACE: dict[ProviderSurface, str] = {
    ProviderSurface.OPENAI_RESPONSES_API: "api.openai.com",
    ProviderSurface.GOOGLE_GEMINI_API: "generativelanguage.googleapis.com",
    ProviderSurface.DEEPSEEK_API: "api.deepseek.com",
    ProviderSurface.OPENROUTER_API: "openrouter.ai",
}


def _require_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a UTC offset")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field_name} must be UTC")
    return value


def _validate_legacy_identity_combination(
    *,
    source_type: SourceType,
    provider_surface: ProviderSurface,
    identity_confidence: IdentityConfidence,
    execution_environment: ExecutionEnvironment,
    runtime: str | None,
    quantization: str | None,
    hardware_profile_id: str | None,
    provider_host: str | None,
) -> None:
    """Apply only the identity rules that existed before migration 0003."""
    if source_type is SourceType.LOCAL_EXACT:
        if execution_environment is not ExecutionEnvironment.LOCAL:
            raise ValueError("local_exact profiles must use the local environment")
        if provider_surface is not ProviderSurface.OLLAMA_LOCAL:
            raise ValueError("local_exact profiles must use the ollama_local surface")
        if identity_confidence is not IdentityConfidence.HIGH:
            raise ValueError("verified local_exact identity requires high confidence")
        if runtime is None or hardware_profile_id is None or quantization is None:
            raise ValueError(
                "local_exact profiles require runtime, hardware_profile_id, and quantization"
            )

    if source_type is SourceType.API_EXACT:
        if execution_environment is not ExecutionEnvironment.CLOUD:
            raise ValueError("api_exact profiles must use the cloud environment")
        if identity_confidence is not IdentityConfidence.HIGH:
            raise ValueError("verified api_exact identity requires high confidence")
        if runtime is None or provider_host is None:
            raise ValueError("api_exact profiles require runtime and provider_host")
        if hardware_profile_id is not None or quantization is not None:
            raise ValueError(
                "cloud api_exact profiles must represent hardware and quantization as None"
            )

    if (
        source_type is SourceType.CLI_EXACT
        and identity_confidence is not IdentityConfidence.MEDIUM
    ):
        raise ValueError("cli_exact identity confidence must be medium")

    if (
        source_type is SourceType.WEB_OPAQUE
        and identity_confidence is not IdentityConfidence.LOW
    ):
        raise ValueError("web_opaque identity confidence must be low")


def _validate_identity_combination(
    *,
    provider: str,
    source_type: SourceType,
    provider_surface: ProviderSurface,
    identity_confidence: IdentityConfidence,
    execution_environment: ExecutionEnvironment,
    runtime: str | None,
    quantization: str | None,
    hardware_profile_id: str | None,
    provider_host: str | None,
    local_model_identity: LocalModelIdentity | None,
    routed_provider_identity: RoutedProviderIdentity | None,
    pricing_snapshot_id: str | None,
    require_material_identity: bool,
) -> None:
    if not require_material_identity:
        _validate_legacy_identity_combination(
            source_type=source_type,
            provider_surface=provider_surface,
            identity_confidence=identity_confidence,
            execution_environment=execution_environment,
            runtime=runtime,
            quantization=quantization,
            hardware_profile_id=hardware_profile_id,
            provider_host=provider_host,
        )
        return

    allowed_surfaces = _ALLOWED_SURFACES_BY_SOURCE[source_type]
    if provider_surface not in allowed_surfaces:
        raise ValueError(
            f"{source_type.value} profiles cannot use the {provider_surface.value} surface"
        )

    expected_confidence = _EXPECTED_CONFIDENCE_BY_SOURCE[source_type]
    if identity_confidence is not expected_confidence:
        raise ValueError(
            f"{source_type.value} identity confidence must be {expected_confidence.value}"
        )

    expected_environment = _EXPECTED_ENVIRONMENT_BY_SOURCE[source_type]
    if execution_environment is not expected_environment:
        raise ValueError(
            f"{source_type.value} profiles must use the "
            f"{expected_environment.value} environment"
        )

    expected_provider = _EXPECTED_PROVIDER_BY_SURFACE.get(provider_surface)
    if expected_provider is not None and provider != expected_provider:
        raise ValueError(
            f"{provider_surface.value} surface requires provider {expected_provider!r}"
        )

    expected_host = _EXPECTED_HOST_BY_API_SURFACE.get(provider_surface)
    if expected_host is not None and provider_host != expected_host:
        raise ValueError(
            f"{provider_surface.value} surface requires provider_host {expected_host!r}"
        )

    if source_type is SourceType.LOCAL_EXACT:
        if (
            runtime is None
            or hardware_profile_id is None
            or quantization is None
            or provider_host is None
        ):
            raise ValueError(
                "local_exact profiles require runtime, hardware_profile_id, quantization, "
                "and provider_host"
            )
        if require_material_identity and local_model_identity is None:
            raise ValueError("local_exact profiles require local_model_identity")
    elif local_model_identity is not None:
        raise ValueError("only local_exact profiles may define local_model_identity")

    if source_type is SourceType.API_EXACT:
        if runtime is None or provider_host is None:
            raise ValueError("api_exact profiles require runtime and provider_host")
        if pricing_snapshot_id is None:
            raise ValueError("api_exact profile requires pricing_snapshot_id")
        if hardware_profile_id is not None or quantization is not None:
            raise ValueError(
                "cloud api_exact profiles must represent hardware and quantization as None"
            )

    if source_type not in (SourceType.LOCAL_EXACT, SourceType.API_EXACT):
        if hardware_profile_id is not None or quantization is not None:
            raise ValueError(
                "non-local profiles must represent hardware and quantization as None"
            )

    if provider_surface is ProviderSurface.OPENROUTER_API:
        if require_material_identity and routed_provider_identity is None:
            raise ValueError("openrouter_api profiles require routed_provider_identity")
        if (
            routed_provider_identity is not None
            and routed_provider_identity.upstream_provider == provider
        ):
            raise ValueError(
                "openrouter_api upstream_provider must identify the upstream, "
                "not openrouter"
            )
    elif routed_provider_identity is not None:
        raise ValueError(
            "only openrouter_api profiles may define routed_provider_identity"
        )


class ModelParameters(BoundaryModel):
    """Provider controls, with unsupported controls represented explicitly by None."""

    temperature: float | None
    max_output_tokens: int | None = Field(ge=1)
    reasoning_mode: str | None
    response_format: str | None
    seed: int | None
    top_p: float | None = Field(ge=0, le=1)
    frequency_penalty: float | None
    presence_penalty: float | None


class ModelProfileReference(BoundaryModel):
    model_profile_id: Identifier
    exact_model_identifier: NonEmptyStr
    displayed_model_name: NonEmptyStr
    provider: Identifier
    provider_surface: ProviderSurface
    provider_host: NonEmptyStr | None
    source_type: SourceType
    collection_method: NonEmptyStr
    model_identity_confidence: IdentityConfidence
    execution_environment: ExecutionEnvironment
    runtime: NonEmptyStr | None
    quantization: NonEmptyStr | None
    hardware_profile_id: Identifier | None
    local_model_identity: LocalModelIdentity | None
    routed_provider_identity: RoutedProviderIdentity | None
    pricing_snapshot_id: Identifier | None
    model_parameters: ModelParameters

    @model_validator(mode="after")
    def validate_identity(self) -> ModelProfileReference:
        _validate_identity_combination(
            provider=self.provider,
            source_type=self.source_type,
            provider_surface=self.provider_surface,
            identity_confidence=self.model_identity_confidence,
            execution_environment=self.execution_environment,
            runtime=self.runtime,
            quantization=self.quantization,
            hardware_profile_id=self.hardware_profile_id,
            provider_host=self.provider_host,
            local_model_identity=self.local_model_identity,
            routed_provider_identity=self.routed_provider_identity,
            pricing_snapshot_id=self.pricing_snapshot_id,
            require_material_identity=True,
        )
        return self


class MissingInformationPolicy(BoundaryModel):
    action: MissingInformationAction
    applies_to_fields: list[NonEmptyStr]


class AcceptanceRules(BoundaryModel):
    allow_semantic_variants: bool
    critical_fields: list[NonEmptyStr]
    forbidden_inventions: list[NonEmptyStr]
    missing_information_policy: MissingInformationPolicy | None
    enum_strict: bool


class ReviewRecord(BoundaryModel):
    reviewer: NonEmptyStr | None
    reviewed_at: datetime | None
    outcome: ReviewOutcome
    notes: str

    @field_validator("reviewed_at")
    @classmethod
    def reviewed_at_is_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _require_utc(value, "reviewed_at")

    @model_validator(mode="after")
    def completed_reviews_have_identity_and_time(self) -> ReviewRecord:
        if self.outcome is not ReviewOutcome.PENDING:
            if self.reviewer is None or self.reviewed_at is None:
                raise ValueError("completed reviews require reviewer and reviewed_at")
        return self


class BenchmarkCase(BoundaryModel):
    case_id: Identifier
    version: SemVer
    suite_version: SemVer
    task_family: TaskFamily
    difficulty: Difficulty
    status: CaseStatus
    author: NonEmptyStr
    author_review: ReviewRecord
    independent_review: ReviewRecord
    tags: list[Identifier]
    input_text: NonEmptyStr
    input_metadata: dict[str, JsonValue] | None
    output_schema: dict[str, JsonValue]
    expected: JsonValue
    acceptance_rules: AcceptanceRules
    notes: str

    @model_validator(mode="after")
    def approved_cases_have_two_distinct_approvals(self) -> BenchmarkCase:
        if self.status is CaseStatus.APPROVED:
            if self.author_review.outcome is not ReviewOutcome.APPROVED:
                raise ValueError("approved cases require an approved author review")
            if self.independent_review.outcome is not ReviewOutcome.APPROVED:
                raise ValueError("approved cases require an approved independent review")
            if self.author_review.reviewer != self.author:
                raise ValueError("author review reviewer must match the case author")
            if self.independent_review.reviewer == self.author:
                raise ValueError("independent reviewer must differ from the author")
        return self


class BenchmarkRequest(BoundaryModel):
    """Exact request given to an adapter; it contains no scoring behavior."""

    run_id: Identifier
    case_id: Identifier
    model_profile_id: Identifier
    system_prompt: NonEmptyStr
    user_prompt: NonEmptyStr
    output_schema: dict[str, JsonValue]
    model_parameters: ModelParameters
    prompt_hash: Sha256
    timeout_seconds: int = Field(ge=1)


class CollectionContext(BoundaryModel):
    """Provenance frozen before collection and copied into each collected run."""

    dataset_version: SemVer
    dataset_commit: GitCommit
    runner_commit: GitCommit
    prompt_version: SemVer
    prompt_hash: Sha256
    exact_model_identifier: NonEmptyStr
    displayed_model_name: NonEmptyStr
    provider: Identifier
    provider_surface: ProviderSurface
    provider_host: NonEmptyStr | None
    collection_method: NonEmptyStr
    model_identity_confidence: IdentityConfidence
    source_type: SourceType
    execution_environment: ExecutionEnvironment
    runtime: NonEmptyStr | None
    quantization: NonEmptyStr | None
    hardware_profile_id: Identifier | None
    local_model_identity: LocalModelIdentity | None
    routed_provider_identity: RoutedProviderIdentity | None
    model_parameters: ModelParameters
    pricing_snapshot_id: Identifier | None

    def _requires_material_identity(self) -> bool:
        return True

    @model_validator(mode="after")
    def validate_identity(self) -> CollectionContext:
        _validate_identity_combination(
            provider=self.provider,
            source_type=self.source_type,
            provider_surface=self.provider_surface,
            identity_confidence=self.model_identity_confidence,
            execution_environment=self.execution_environment,
            runtime=self.runtime,
            quantization=self.quantization,
            hardware_profile_id=self.hardware_profile_id,
            provider_host=self.provider_host,
            local_model_identity=self.local_model_identity,
            routed_provider_identity=self.routed_provider_identity,
            pricing_snapshot_id=self.pricing_snapshot_id,
            require_material_identity=self._requires_material_identity(),
        )
        return self


class PlannedRun(CollectionContext):
    run_id: Identifier
    batch_id: Identifier
    case_id: Identifier
    case_version: SemVer
    model_profile_id: Identifier
    rep_index: int = Field(ge=0)
    run_order_seed: int
    profile_provenance_complete: bool

    def _requires_material_identity(self) -> bool:
        return self.profile_provenance_complete


_ADAPTER_RESPONSE_VALIDATION_TOKEN = object()


@dataclass(frozen=True)
class _AdapterResponseValidationContext:
    planned_run: PlannedRun
    token: object


class BenchmarkBatch(BoundaryModel):
    """Frozen batch configuration and lifecycle counters."""

    batch_id: Identifier
    batch_purpose: BatchPurpose
    dataset_version: SemVer
    dataset_commit: GitCommit
    runner_commit: GitCommit
    prompt_version: SemVer
    run_order_seed: int
    operator: NonEmptyStr
    environment: NonEmptyStr
    status: BatchStatus
    started_at: datetime | None
    completed_at: datetime | None
    invalid_run_count: int = Field(ge=0)
    valid_for_scoring_count: int = Field(ge=0)

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None, info: Any) -> datetime | None:
        return None if value is None else _require_utc(value, info.field_name)

    @model_validator(mode="after")
    def validate_status_timestamps(self) -> BenchmarkBatch:
        if self.status is BatchStatus.PLANNED:
            if self.started_at is not None or self.completed_at is not None:
                raise ValueError(
                    "planned batches require started_at and completed_at to be None"
                )
        elif self.status is BatchStatus.RUNNING:
            if self.started_at is None or self.completed_at is not None:
                raise ValueError(
                    "running batches require started_at and completed_at=None"
                )
        elif self.status in (BatchStatus.COMPLETED, BatchStatus.FROZEN):
            if self.started_at is None or self.completed_at is None:
                raise ValueError(
                    "completed or frozen batches require started_at and completed_at"
                )
        if self.started_at is not None and self.completed_at is not None:
            if self.completed_at < self.started_at:
                raise ValueError("completed_at cannot precede started_at")
        return self


class ArtifactRef(BoundaryModel):
    """Immutable filesystem reference returned by ArtifactStore.write_immutable."""

    run_id: Identifier
    storage_ref: NonEmptyStr
    checksum: Sha256
    byte_length: int = Field(ge=0)
    media_type: NonEmptyStr = "application/octet-stream"


class RawArtifactReference(BoundaryModel):
    raw_id: Identifier
    run_id: Identifier
    raw_artifact_ref: NonEmptyStr
    raw_checksum: Sha256
    byte_length: int = Field(ge=0)
    media_type: NonEmptyStr
    redaction_status: RedactionStatus


class NormalizedAdapterResponse(CollectionContext):
    """Collection result only; parsing, repair, scoring, and verdicts are excluded."""

    model_config = ConfigDict(frozen=True)

    run_id: Identifier
    case_id: Identifier
    model_profile_id: Identifier
    run_timestamp: datetime
    started_at: datetime
    first_token_at: datetime | None
    completed_at: datetime
    latency_ms: int = Field(ge=0)
    input_tokens: int | None = Field(ge=0)
    output_tokens: int | None = Field(ge=0)
    token_count_inferred: bool
    raw_artifact_ref: NonEmptyStr | None
    raw_checksum: Sha256 | None
    error_type: ErrorType
    error_message: str | None

    retry_count: int = Field(ge=0, le=3)
    estimated_cost: Decimal | None = Field(ge=0)
    runtime_metadata: dict[str, JsonValue] | None
    hardware_metadata: dict[str, JsonValue] | None
    provider_request_id: str | None

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> NormalizedAdapterResponse:
        if update is not None:
            raise TypeError(
                "NormalizedAdapterResponse is immutable; construct a new response "
                "with from_planned_run"
            )
        return super().model_copy(deep=deep)

    @classmethod
    def from_planned_run(
        cls,
        planned_run: PlannedRun,
        *,
        pricing_catalog: PricingSnapshotCatalog | None = None,
        run_timestamp: datetime,
        started_at: datetime,
        first_token_at: datetime | None,
        completed_at: datetime,
        latency_ms: int,
        input_tokens: int | None,
        output_tokens: int | None,
        token_count_inferred: bool,
        raw_artifact_ref: str | None,
        raw_checksum: str | None,
        error_type: ErrorType,
        error_message: str | None,
        retry_count: int,
        estimated_cost: Decimal | None,
        runtime_metadata: dict[str, JsonValue] | None,
        hardware_metadata: dict[str, JsonValue] | None,
        provider_request_id: str | None,
    ) -> NormalizedAdapterResponse:
        """Bind collected output to a fully validated planned-run provenance record."""
        validated_run = PlannedRun.model_validate(
            planned_run.model_dump(mode="python")
        )
        if not validated_run.profile_provenance_complete:
            raise ValueError("collected responses require complete profile provenance")

        requires_pricing_catalog = (
            validated_run.source_type is SourceType.API_EXACT
            or validated_run.pricing_snapshot_id is not None
        )
        if pricing_catalog is None:
            if requires_pricing_catalog:
                raise ValueError(
                    "API or priced collected responses require a PricingSnapshotCatalog"
                )
        else:
            from goodenough_bench.profile_loaders import PricingSnapshotCatalog

            validated_catalog = PricingSnapshotCatalog.model_validate(
                pricing_catalog.model_dump(mode="python")
            )
            validated_catalog.validate_profile_reference(validated_run)

        response_data: dict[str, object] = {
            **validated_run.model_dump(
                mode="python",
                include=set(CollectionContext.model_fields),
            ),
            "run_id": validated_run.run_id,
            "case_id": validated_run.case_id,
            "model_profile_id": validated_run.model_profile_id,
            "run_timestamp": run_timestamp,
            "started_at": started_at,
            "first_token_at": first_token_at,
            "completed_at": completed_at,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "token_count_inferred": token_count_inferred,
            "raw_artifact_ref": raw_artifact_ref,
            "raw_checksum": raw_checksum,
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": retry_count,
            "estimated_cost": estimated_cost,
            "runtime_metadata": runtime_metadata,
            "hardware_metadata": hardware_metadata,
            "provider_request_id": provider_request_id,
        }
        return cls.model_validate(
            response_data,
            context=_AdapterResponseValidationContext(
                planned_run=validated_run,
                token=_ADAPTER_RESPONSE_VALIDATION_TOKEN,
            ),
        )

    @model_validator(mode="after")
    def require_validated_planned_run(
        self,
        info: ValidationInfo,
    ) -> NormalizedAdapterResponse:
        context = info.context
        if (
            not isinstance(context, _AdapterResponseValidationContext)
            or context.token is not _ADAPTER_RESPONSE_VALIDATION_TOKEN
        ):
            raise ValueError(
                "collected responses must be constructed with from_planned_run"
            )
        planned_run = context.planned_run
        mismatches = [
            field_name
            for field_name in CollectionContext.model_fields
            if getattr(self, field_name) != getattr(planned_run, field_name)
        ]
        for field_name in ("run_id", "case_id", "model_profile_id"):
            if getattr(self, field_name) != getattr(planned_run, field_name):
                mismatches.append(field_name)
        if mismatches:
            fields = ", ".join(mismatches)
            raise ValueError(
                "collected response provenance conflicts with planned run for: "
                f"{fields}"
            )
        return self

    @field_validator("run_timestamp", "started_at", "first_token_at", "completed_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None, info: Any) -> datetime | None:
        return None if value is None else _require_utc(value, info.field_name)

    @model_validator(mode="after")
    def validate_collection_result(self) -> NormalizedAdapterResponse:
        if self.run_timestamp != self.started_at:
            raise ValueError("run_timestamp must equal started_at")
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if self.first_token_at is not None and not (
            self.started_at <= self.first_token_at <= self.completed_at
        ):
            raise ValueError("first_token_at must fall within the run interval")
        if (self.raw_artifact_ref is None) != (self.raw_checksum is None):
            raise ValueError("raw artifact reference and checksum must be present together")
        if self.error_type is ErrorType.NONE and self.raw_artifact_ref is None:
            raise ValueError("successful collection requires a checksummed raw artifact")
        if self.error_type is ErrorType.NONE and self.error_message is not None:
            raise ValueError("successful collection must use error_message=None")
        if self.error_type is not ErrorType.NONE and self.error_message is None:
            raise ValueError("failed collection requires an error message")
        if self.error_type is ErrorType.PARSE_FAILURE:
            raise ValueError("parse_failure belongs to ParseBoundaryRecord, not adapter output")
        if (self.input_tokens is None or self.output_tokens is None) and not self.token_count_inferred:
            raise ValueError("missing token counts require token_count_inferred=true")
        return self


# Architecture-level name retained for the future ModelAdapter protocol.
BenchmarkResponse = NormalizedAdapterResponse


class ParseBoundaryRecord(BoundaryModel):
    parsed_id: Identifier
    run_id: Identifier
    raw_artifact_ref: NonEmptyStr
    raw_checksum: Sha256
    parser_version: SemVer
    parse_success: bool
    parsed_json: JsonValue | None
    parse_errors: list[NonEmptyStr]
    schema_valid: bool | None
    schema_errors: list[NonEmptyStr]

    @model_validator(mode="after")
    def validate_parse_result(self) -> ParseBoundaryRecord:
        if self.parse_success:
            if self.parsed_json is None or self.parse_errors:
                raise ValueError(
                    "successful parse requires parsed_json and no parse errors"
                )
        elif self.parsed_json is not None or not self.parse_errors:
            raise ValueError("failed parse requires no parsed_json and at least one error")
        if not self.parse_success and self.schema_valid is not None:
            raise ValueError("schema_valid must be None when parsing failed")
        if self.schema_valid is not False and self.schema_errors:
            raise ValueError("schema errors are allowed only when schema_valid is false")
        if self.schema_valid is False and not self.schema_errors:
            raise ValueError("schema-invalid records require at least one schema error")
        return self


class HumanOverride(BoundaryModel):
    override_id: Identifier
    run_id: Identifier
    reviewer: NonEmptyStr
    timestamp: datetime
    field_changed: NonEmptyStr
    original_value: JsonValue
    new_value: JsonValue
    reason: NonEmptyStr

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return _require_utc(value, "timestamp")


class ScoreBoundaryRecord(BoundaryModel):
    score_id: Identifier
    run_id: Identifier
    parsed_id: Identifier
    task_family: TaskFamily
    scorer_version: SemVer
    metrics: dict[str, Decimal | int | bool | None]
    case_pass: bool
    failure_reasons: list[NonEmptyStr]
    result_checksum: Sha256
    human_overrides: list[HumanOverride]

    @model_validator(mode="after")
    def passing_scores_have_no_failure_reasons(self) -> ScoreBoundaryRecord:
        if self.case_pass and self.failure_reasons:
            raise ValueError("passing score records cannot contain failure reasons")
        if not self.case_pass and not self.failure_reasons:
            raise ValueError("failing score records require at least one failure reason")
        return self
