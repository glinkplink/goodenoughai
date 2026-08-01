"""Strongly typed boundaries for the benchmark lifecycle.

These models describe data exchanged between planning, collection, artifact,
parsing, and scoring components. They do not implement those components.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    field_validator,
    model_validator,
)


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


def _require_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a UTC offset")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field_name} must be UTC")
    return value


def _validate_identity_combination(
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

    if source_type is SourceType.CLI_EXACT and identity_confidence is not IdentityConfidence.MEDIUM:
        raise ValueError("cli_exact identity confidence must be medium")

    if source_type is SourceType.WEB_OPAQUE and identity_confidence is not IdentityConfidence.LOW:
        raise ValueError("web_opaque identity confidence must be low")


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
    pricing_snapshot_id: Identifier | None
    model_parameters: ModelParameters

    @model_validator(mode="after")
    def validate_identity(self) -> ModelProfileReference:
        _validate_identity_combination(
            source_type=self.source_type,
            provider_surface=self.provider_surface,
            identity_confidence=self.model_identity_confidence,
            execution_environment=self.execution_environment,
            runtime=self.runtime,
            quantization=self.quantization,
            hardware_profile_id=self.hardware_profile_id,
            provider_host=self.provider_host,
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
    model_parameters: ModelParameters
    pricing_snapshot_id: Identifier | None

    @model_validator(mode="after")
    def validate_identity(self) -> CollectionContext:
        _validate_identity_combination(
            source_type=self.source_type,
            provider_surface=self.provider_surface,
            identity_confidence=self.model_identity_confidence,
            execution_environment=self.execution_environment,
            runtime=self.runtime,
            quantization=self.quantization,
            hardware_profile_id=self.hardware_profile_id,
            provider_host=self.provider_host,
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
