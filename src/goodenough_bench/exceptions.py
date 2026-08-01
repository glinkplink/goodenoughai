"""Repository, migration, and artifact store error types."""

from __future__ import annotations


class RepositoryError(Exception):
    """Base class for repository failures."""


class RepositoryConflictError(RepositoryError):
    """Raised when a create would contradict persisted state."""


class MigrationError(Exception):
    """Raised when migration discovery or application fails."""


class ArtifactError(Exception):
    """Base class for artifact store failures."""


class ArtifactConflictError(ArtifactError):
    """Raised when an immutable write would replace existing run bytes."""


class ArtifactCorruptionError(ArtifactError):
    """Raised when stored bytes are missing or fail checksum verification."""


class ConfigLoadError(Exception):
    """Raised when a tracked config document fails validation."""
