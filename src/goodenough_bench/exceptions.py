"""Repository and migration error types."""

from __future__ import annotations


class RepositoryError(Exception):
    """Base class for repository failures."""


class RepositoryConflictError(RepositoryError):
    """Raised when a create would contradict persisted state."""


class MigrationError(Exception):
    """Raised when migration discovery or application fails."""
