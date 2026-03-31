"""Data contracts for raw and interim RideFare datasets."""

from __future__ import annotations

import warnings
from collections.abc import Iterable

warnings.filterwarnings(
    "ignore",
    message="Pandas and numpy have been removed from the base pandera",
    category=UserWarning,
)

import pandera.errors
import pandera.polars as pa
import polars as pl

from ridefare.exceptions import MissingInputError, SchemaValidationError

RIDES_COLUMN_TYPES: dict[str, pl.DataType] = {
    "distance": pl.Float64,
    "cab_type": pl.String,
    "time_stamp": pl.Int64,
    "destination": pl.String,
    "source": pl.String,
    "price": pl.Float64,
    "surge_multiplier": pl.Float64,
    "name": pl.String,
}

WEATHER_COLUMN_TYPES: dict[str, pl.DataType] = {
    "temp": pl.Float64,
    "clouds": pl.Float64,
    "pressure": pl.Float64,
    "rain": pl.Float64,
    "humidity": pl.Float64,
    "wind": pl.Float64,
    "location": pl.String,
    "time_stamp": pl.Int64,
}

RIDES_REQUIRED_COLUMNS = tuple(RIDES_COLUMN_TYPES)
WEATHER_REQUIRED_COLUMNS = tuple(WEATHER_COLUMN_TYPES)

RIDES_CRITICAL_FIELDS = RIDES_REQUIRED_COLUMNS
WEATHER_CRITICAL_FIELDS = ("location", "time_stamp")

RIDES_SCHEMA = pa.DataFrameSchema(
    {
        "distance": pa.Column(float, nullable=False),
        "cab_type": pa.Column(str, nullable=False),
        "time_stamp": pa.Column(int, nullable=False),
        "destination": pa.Column(str, nullable=False),
        "source": pa.Column(str, nullable=False),
        "price": pa.Column(float, nullable=False),
        "surge_multiplier": pa.Column(float, nullable=False),
        "name": pa.Column(str, nullable=False),
    },
    strict=True,
)

WEATHER_SCHEMA = pa.DataFrameSchema(
    {
        "temp": pa.Column(float, nullable=True),
        "clouds": pa.Column(float, nullable=True),
        "pressure": pa.Column(float, nullable=True),
        "rain": pa.Column(float, nullable=True),
        "humidity": pa.Column(float, nullable=True),
        "wind": pa.Column(float, nullable=True),
        "location": pa.Column(str, nullable=False),
        "time_stamp": pa.Column(int, nullable=False),
    },
    strict=True,
)


def ensure_required_columns(
    frame: pl.DataFrame,
    required_columns: Iterable[str],
    dataset_name: str,
) -> None:
    """Raise when a required input column is missing."""

    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise MissingInputError(
            f"{dataset_name} is missing required column(s): {joined}"
        )


def drop_rows_missing_fields(frame: pl.DataFrame, critical_fields: Iterable[str]) -> pl.DataFrame:
    """Drop rows that are missing critical fields."""

    return frame.drop_nulls(list(critical_fields))


def validate_rides(frame: pl.DataFrame) -> pl.DataFrame:
    """Validate the rides contract."""

    return _validate_schema(frame, schema=RIDES_SCHEMA, dataset_name="rides")


def validate_weather(frame: pl.DataFrame) -> pl.DataFrame:
    """Validate the weather contract."""

    return _validate_schema(frame, schema=WEATHER_SCHEMA, dataset_name="weather")


def _validate_schema(
    frame: pl.DataFrame,
    schema: pa.DataFrameSchema,
    dataset_name: str,
) -> pl.DataFrame:
    try:
        return schema.validate(frame)
    except (pandera.errors.SchemaError, pandera.errors.SchemaErrors) as exc:
        raise SchemaValidationError(f"{dataset_name} failed schema validation: {exc}") from exc
