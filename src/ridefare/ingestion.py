"""Ingestion flow for raw RideFare CSV datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from ridefare.config import IngestConfig
from ridefare.contracts import (
    RIDES_COLUMN_TYPES,
    RIDES_CRITICAL_FIELDS,
    RIDES_REQUIRED_COLUMNS,
    WEATHER_COLUMN_TYPES,
    WEATHER_CRITICAL_FIELDS,
    WEATHER_REQUIRED_COLUMNS,
    drop_rows_missing_fields,
    ensure_required_columns,
    validate_rides,
    validate_weather,
)
from ridefare.exceptions import MissingInputError
from ridefare.normalization import cast_columns, normalize_column_names, select_columns


@dataclass(frozen=True)
class IngestResult:
    """Outputs produced by a successful ingest command."""

    rides_parquet_path: Path
    weather_parquet_path: Path
    manifest_path: Path


def run_ingest(config: IngestConfig) -> IngestResult:
    """Run the raw-to-interim ingestion flow."""

    validate_input_files(config)
    config.interim_dir.mkdir(parents=True, exist_ok=True)

    rides_frame = prepare_rides_frame(config.rides_path)
    weather_frame = prepare_weather_frame(config.weather_path)

    rides_parquet_path = config.interim_dir / "rides.parquet"
    weather_parquet_path = config.interim_dir / "weather.parquet"

    rides_frame.write_parquet(rides_parquet_path)
    weather_frame.write_parquet(weather_parquet_path)

    manifest = build_run_manifest(
        rides_path=rides_parquet_path,
        rides_frame=rides_frame,
        weather_path=weather_parquet_path,
        weather_frame=weather_frame,
    )
    config.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return IngestResult(
        rides_parquet_path=rides_parquet_path,
        weather_parquet_path=weather_parquet_path,
        manifest_path=config.manifest_path,
    )


def validate_input_files(config: IngestConfig) -> None:
    """Validate that the expected raw CSV files exist."""

    missing_files = [
        path.name
        for path in (config.rides_path, config.weather_path)
        if not path.exists()
    ]
    if missing_files:
        joined = ", ".join(missing_files)
        raise MissingInputError(f"Missing required raw input file(s): {joined}")


def prepare_rides_frame(csv_path: Path) -> pl.DataFrame:
    """Read, normalize, and validate rides input."""

    raw_frame = pl.read_csv(csv_path)
    normalized = normalize_column_names(raw_frame)
    ensure_required_columns(normalized, RIDES_REQUIRED_COLUMNS, dataset_name="rides")
    selected = select_columns(normalized, RIDES_REQUIRED_COLUMNS)
    casted = cast_columns(selected, RIDES_COLUMN_TYPES)
    deduplicated = casted.unique(maintain_order=True)
    cleaned = drop_rows_missing_fields(deduplicated, RIDES_CRITICAL_FIELDS)
    return validate_rides(cleaned)


def prepare_weather_frame(csv_path: Path) -> pl.DataFrame:
    """Read, normalize, and validate weather input."""

    raw_frame = pl.read_csv(csv_path)
    normalized = normalize_column_names(raw_frame)
    ensure_required_columns(normalized, WEATHER_REQUIRED_COLUMNS, dataset_name="weather")
    selected = select_columns(normalized, WEATHER_REQUIRED_COLUMNS)
    casted = cast_columns(selected, WEATHER_COLUMN_TYPES)
    deduplicated = casted.unique(maintain_order=True)
    cleaned = drop_rows_missing_fields(deduplicated, WEATHER_CRITICAL_FIELDS)
    return validate_weather(cleaned)


def build_run_manifest(
    rides_path: Path,
    rides_frame: pl.DataFrame,
    weather_path: Path,
    weather_frame: pl.DataFrame,
) -> dict[str, object]:
    """Build a small machine-readable summary of an ingest run."""

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "datasets": {
            "rides": {
                "path": str(rides_path),
                "rows": rides_frame.height,
                "columns": rides_frame.columns,
            },
            "weather": {
                "path": str(weather_path),
                "rows": weather_frame.height,
                "columns": weather_frame.columns,
            },
        },
    }
