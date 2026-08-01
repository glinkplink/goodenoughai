"""GoodEnough.ai local benchmark foundation."""

from .boundaries import (
    AcceptanceRules,
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

__all__ = [
    "AcceptanceRules",
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
    "ScoreBoundaryRecord",
    "SourceType",
    "TaskFamily",
]

__version__ = "0.1.0"
