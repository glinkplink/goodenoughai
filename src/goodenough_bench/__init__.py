"""GoodEnough.ai local benchmark foundation."""

from .boundaries import (
    AcceptanceRules,
    BatchPurpose,
    BatchStatus,
    BenchmarkBatch,
    BenchmarkCase,
    BenchmarkRequest,
    BenchmarkResponse,
    CollectionContext,
    ErrorType,
    HumanOverride,
    IdentityConfidence,
    ModelParameters,
    ModelProfileReference,
    NormalizedAdapterResponse,
    ParseBoundaryRecord,
    PlannedRun,
    ProviderSurface,
    RawArtifactReference,
    ScoreBoundaryRecord,
    SourceType,
    TaskFamily,
)
from .repository import Repository, SQLiteRepository

__all__ = [
    "AcceptanceRules",
    "BatchPurpose",
    "BatchStatus",
    "BenchmarkBatch",
    "BenchmarkCase",
    "BenchmarkRequest",
    "BenchmarkResponse",
    "CollectionContext",
    "ErrorType",
    "HumanOverride",
    "IdentityConfidence",
    "ModelParameters",
    "ModelProfileReference",
    "NormalizedAdapterResponse",
    "ParseBoundaryRecord",
    "PlannedRun",
    "ProviderSurface",
    "RawArtifactReference",
    "Repository",
    "ScoreBoundaryRecord",
    "SQLiteRepository",
    "SourceType",
    "TaskFamily",
]

__version__ = "0.1.0"
