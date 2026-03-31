"""Contracts and dataclasses for the RideFare ML workflow."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FeatureContract:
    """Canonical feature contract sourced from mart_model_features."""

    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    target_column: str
    time_column: str
    identifier_column: str

    @property
    def feature_columns(self) -> tuple[str, ...]:
        return self.numeric_features + self.categorical_features

    @property
    def required_columns(self) -> tuple[str, ...]:
        return (
            self.identifier_column,
            self.time_column,
            *self.feature_columns,
            self.target_column,
        )


def default_feature_contract() -> FeatureContract:
    """Return the stable Phase 3 feature contract."""

    return FeatureContract(
        numeric_features=(
            "distance",
            "surge_multiplier",
            "temp",
            "clouds",
            "pressure",
            "rain",
            "humidity",
            "wind",
            "ride_hour_of_day",
            "ride_day_of_week",
        ),
        categorical_features=("source", "destination", "cab_type", "ride_name"),
        target_column="price",
        time_column="ride_hour",
        identifier_column="ride_id",
    )


@dataclass(frozen=True)
class DatasetMetadata:
    """Descriptive metadata about the modeling dataset."""

    row_count: int
    feature_columns: tuple[str, ...]
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    null_counts: dict[str, int]
    time_range: dict[str, str | None]
    fingerprint: str
    target_column: str
    time_column: str
    identifier_column: str


@dataclass(frozen=True)
class ModelingDataset:
    """Materialized modeling dataset ready for training."""

    frame: pd.DataFrame
    features: pd.DataFrame
    target: pd.Series
    metadata: DatasetMetadata
    contract: FeatureContract
