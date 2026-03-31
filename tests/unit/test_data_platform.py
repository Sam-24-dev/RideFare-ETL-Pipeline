from __future__ import annotations

from pathlib import Path

import polars as pl


def test_default_paths_match_phase_two_contract() -> None:
    from ridefare.config import RideFarePaths

    project_root = Path("C:/tmp/ridefare")

    paths = RideFarePaths.defaults(project_root=project_root)

    assert paths.rides_raw_path == project_root / "data" / "raw" / "PFDA_rides.csv"
    assert paths.weather_raw_path == project_root / "data" / "raw" / "PFDA_weather.csv"
    assert paths.interim_dir == project_root / "data" / "interim"
    assert paths.duckdb_path == project_root / "data" / "processed" / "ridefare.duckdb"


def test_normalize_column_names_trims_and_snake_cases_headers() -> None:
    from ridefare.normalization import normalize_column_names

    frame = pl.DataFrame({" Ride Name ": ["UberX"], "Surge Multiplier": [1.2]})

    normalized = normalize_column_names(frame)

    assert normalized.columns == ["ride_name", "surge_multiplier"]


def test_add_time_buckets_respects_legacy_timestamp_units() -> None:
    from ridefare.transform import add_time_buckets

    rides = pl.DataFrame({"time_stamp": [1711888200000], "source": ["North End"]})
    weather = pl.DataFrame({"time_stamp": [1711888200], "location": ["North End"]})

    rides_bucketed = add_time_buckets(rides, dataset_name="rides")
    weather_bucketed = add_time_buckets(weather, dataset_name="weather")

    assert rides_bucketed["ride_hour"].to_list()[0].isoformat() == "2024-03-31T12:00:00"
    assert weather_bucketed["weather_hour"].to_list()[0].isoformat() == "2024-03-31T12:00:00"
