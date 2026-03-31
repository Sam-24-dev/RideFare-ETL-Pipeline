"""Transformation flow for interim RideFare parquet datasets."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import duckdb
import polars as pl

from ridefare.config import TransformConfig
from ridefare.exceptions import DbtBuildError, MissingArtifactError


@dataclass(frozen=True)
class TransformResult:
    """Outputs produced by a successful transform command."""

    duckdb_path: Path
    dbt_profiles_path: Path


def run_transform(config: TransformConfig) -> TransformResult:
    """Load interim parquet data, prepare DuckDB raw tables, and run dbt build."""

    rides_path = config.interim_dir / "rides.parquet"
    weather_path = config.interim_dir / "weather.parquet"
    validate_interim_artifacts(rides_path, weather_path)

    rides_frame = prepare_raw_rides(pl.read_parquet(rides_path))
    weather_frame = prepare_raw_weather(pl.read_parquet(weather_path))

    config.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    config.dbt_profiles_dir.mkdir(parents=True, exist_ok=True)

    write_raw_tables(
        duckdb_path=config.duckdb_path,
        rides_frame=rides_frame,
        weather_frame=weather_frame,
        working_dir=config.duckdb_path.parent,
    )
    profiles_path = write_dbt_profile(config)
    run_dbt_build(config)

    return TransformResult(
        duckdb_path=config.duckdb_path,
        dbt_profiles_path=profiles_path,
    )


def add_time_buckets(frame: pl.DataFrame, dataset_name: str) -> pl.DataFrame:
    """Add normalized timestamps and hourly buckets preserving legacy timestamp units."""

    if dataset_name == "rides":
        timestamp_expression = pl.from_epoch(pl.col("time_stamp"), time_unit="ms")
        return frame.with_columns(
            timestamp_expression.alias("ride_timestamp"),
            timestamp_expression.dt.truncate("1h").alias("ride_hour"),
        )

    if dataset_name == "weather":
        timestamp_expression = pl.from_epoch(pl.col("time_stamp"), time_unit="s")
        return frame.with_columns(
            timestamp_expression.alias("weather_timestamp"),
            timestamp_expression.dt.truncate("1h").alias("weather_hour"),
        )

    message = f"Unsupported dataset for bucketing: {dataset_name}"
    raise ValueError(message)


def prepare_raw_rides(frame: pl.DataFrame) -> pl.DataFrame:
    """Prepare rides data for raw loading into DuckDB."""

    bucketed = add_time_buckets(frame, dataset_name="rides")
    return bucketed.with_row_index("ride_id", offset=1).select(
        "ride_id",
        "distance",
        "cab_type",
        "time_stamp",
        "ride_timestamp",
        "ride_hour",
        "destination",
        "source",
        "price",
        "surge_multiplier",
        "name",
    )


def prepare_raw_weather(frame: pl.DataFrame) -> pl.DataFrame:
    """Prepare weather data for raw loading into DuckDB."""

    bucketed = add_time_buckets(frame, dataset_name="weather")
    return bucketed.with_row_index("weather_id", offset=1).select(
        "weather_id",
        "temp",
        "clouds",
        "pressure",
        "rain",
        "humidity",
        "wind",
        "location",
        "time_stamp",
        "weather_timestamp",
        "weather_hour",
    )


def validate_interim_artifacts(rides_path: Path, weather_path: Path) -> None:
    """Raise when expected interim parquet files are missing."""

    missing = [path.name for path in (rides_path, weather_path) if not path.exists()]
    if missing:
        raise MissingArtifactError(
            f"Missing interim artifact(s): {', '.join(missing)}"
        )


def write_raw_tables(
    duckdb_path: Path,
    rides_frame: pl.DataFrame,
    weather_frame: pl.DataFrame,
    working_dir: Path,
) -> None:
    """Load prepared raw parquet snapshots into DuckDB tables."""

    with tempfile.TemporaryDirectory(dir=working_dir) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        rides_temp_path = temp_dir / "raw_rides.parquet"
        weather_temp_path = temp_dir / "raw_weather.parquet"
        rides_frame.write_parquet(rides_temp_path)
        weather_frame.write_parquet(weather_temp_path)

        conn = duckdb.connect(str(duckdb_path))
        try:
            conn.execute(
                "create or replace table raw_rides as select * from read_parquet(?)",
                [str(rides_temp_path)],
            )
            conn.execute(
                "create or replace table raw_weather as select * from read_parquet(?)",
                [str(weather_temp_path)],
            )
        finally:
            conn.close()


def write_dbt_profile(config: TransformConfig) -> Path:
    """Materialize a local dbt profile tied to the requested DuckDB file."""

    profiles_path = config.dbt_profiles_dir / "profiles.yml"
    profile_text = (
        "ridefare:\n"
        "  target: dev\n"
        "  outputs:\n"
        "    dev:\n"
        "      type: duckdb\n"
        f"      path: {config.duckdb_path.as_posix()}\n"
        "      threads: 4\n"
    )
    profiles_path.write_text(profile_text, encoding="utf-8")
    return profiles_path


def run_dbt_build(config: TransformConfig) -> None:
    """Run dbt build using the current Python interpreter."""

    command = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "build",
        "--project-dir",
        str(config.dbt_project_dir),
        "--profiles-dir",
        str(config.dbt_profiles_dir),
        "--target",
        "dev",
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        combined_output = "\n".join(
            part for part in (completed.stdout.strip(), completed.stderr.strip()) if part
        )
        raise DbtBuildError(f"dbt build failed.\n{combined_output}")
