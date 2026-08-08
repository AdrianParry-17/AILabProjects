"""Project-wide exception hierarchy (CONVENTION.md § 6.1).

Layer owners subclass the domain root that matches their layer. Generic utilities
raise stdlib exceptions (`ValueError`, `KeyError`, ...) unless a domain root is
genuinely needed by a caller.
"""

from __future__ import annotations


class AILabError(Exception):
    """Base for all project-specific failures."""


class ConfigError(AILabError):
    """Configuration/path/default failures (config layer)."""


class DataError(AILabError):
    """Dataset/pipeline failures (data layer)."""


class InvalidGraphError(DataError):
    """A graph violates its schema or referential integrity."""


class SearchError(AILabError):
    """Search framework/algorithm failures (core/algorithms layer)."""


class UnreachableNodeError(SearchError):
    """Raised by weighted searches when the goal is unreachable."""
