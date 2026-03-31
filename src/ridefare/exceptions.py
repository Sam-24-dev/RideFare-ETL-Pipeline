"""Project-specific exceptions for the RideFare data platform."""

from __future__ import annotations


class RideFareError(Exception):
    """Base exception for operational RideFare failures."""


class MissingInputError(RideFareError):
    """Raised when required raw inputs are missing."""


class MissingArtifactError(RideFareError):
    """Raised when an expected pipeline artifact is missing."""


class SchemaValidationError(RideFareError):
    """Raised when a dataframe does not satisfy the declared contract."""


class DbtBuildError(RideFareError):
    """Raised when dbt build fails."""
