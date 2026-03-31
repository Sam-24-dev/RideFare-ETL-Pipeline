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


class ModelingDataError(RideFareError):
    """Raised when the modeled dataset cannot support the ML workflow."""


class TrainingPipelineError(RideFareError):
    """Raised when the ML training workflow fails."""


class ExportArtifactsError(RideFareError):
    """Raised when web export artifacts cannot be produced."""
