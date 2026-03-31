"""Dataset loading and feature contract enforcement for RideFare ML."""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb
import pandas as pd

from ridefare.exceptions import MissingArtifactError, ModelingDataError
from ridefare.ml_contracts import DatasetMetadata, ModelingDataset, default_feature_contract

MODEL_SOURCE_QUERY = """
select
  ride_id,
  ride_hour,
  source,
  destination,
  cab_type,
  ride_name,
  distance,
  surge_multiplier,
  temp,
  clouds,
  pressure,
  rain,
  humidity,
  wind,
  price,
  ride_hour_of_day,
  ride_day_of_week
from mart_model_features
order by ride_hour, ride_id
"""


def load_modeling_frame(duckdb_path: Path) -> pd.DataFrame:
    """Load the canonical modeling mart from DuckDB into pandas."""

    if not duckdb_path.exists():
        raise MissingArtifactError(f"Missing DuckDB database: {duckdb_path}")

    conn = duckdb.connect(str(duckdb_path))
    try:
        tables = {row[0] for row in conn.execute("show tables").fetchall()}
        if "mart_model_features" not in tables:
            raise MissingArtifactError(
                f"Missing modeled dataset 'mart_model_features' in {duckdb_path}"
            )
        frame = conn.execute(MODEL_SOURCE_QUERY).fetch_df()
    finally:
        conn.close()

    return frame


def build_modeling_dataset(frame: pd.DataFrame) -> ModelingDataset:
    """Validate and structure the modeling dataset."""

    contract = default_feature_contract()
    missing_columns = [
        column for column in contract.required_columns if column not in frame.columns
    ]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ModelingDataError(f"Modeling dataset is missing required columns: {joined}")

    if frame.empty:
        raise ModelingDataError("Modeling dataset is empty.")

    ordered = frame.loc[:, contract.required_columns].copy()
    ordered[contract.time_column] = pd.to_datetime(ordered[contract.time_column], utc=False)
    ordered = ordered.sort_values(
        by=[contract.time_column, contract.identifier_column],
        kind="stable",
    ).reset_index(drop=True)

    time_min = ordered[contract.time_column].min()
    time_max = ordered[contract.time_column].max()
    metadata = DatasetMetadata(
        row_count=len(ordered),
        feature_columns=contract.feature_columns,
        numeric_features=contract.numeric_features,
        categorical_features=contract.categorical_features,
        null_counts={
            column: int(ordered[column].isna().sum())
            for column in contract.required_columns
        },
        time_range={
            "min": None if pd.isna(time_min) else time_min.isoformat(),
            "max": None if pd.isna(time_max) else time_max.isoformat(),
        },
        fingerprint=build_dataset_fingerprint(ordered, contract),
        target_column=contract.target_column,
        time_column=contract.time_column,
        identifier_column=contract.identifier_column,
    )
    return ModelingDataset(
        frame=ordered,
        features=ordered.loc[:, contract.feature_columns].copy(),
        target=ordered.loc[:, contract.target_column].copy(),
        metadata=metadata,
        contract=contract,
    )


def build_dataset_fingerprint(frame: pd.DataFrame, contract) -> str:
    """Generate a stable fingerprint over the ordered modeling dataset."""

    digest = hashlib.sha256()
    digest.update("|".join(contract.required_columns).encode("utf-8"))
    for row in frame.itertuples(index=False, name=None):
        values = []
        for item in row:
            if pd.isna(item):
                values.append("")
            elif hasattr(item, "isoformat"):
                values.append(item.isoformat())
            else:
                values.append(str(item))
        digest.update("|".join(values).encode("utf-8"))
    return digest.hexdigest()
