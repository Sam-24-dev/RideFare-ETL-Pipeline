from __future__ import annotations

import json
import shutil
from pathlib import Path

import duckdb
import polars as pl
import pytest


@pytest.fixture
def sample_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project_root = Path(__file__).resolve().parents[2]
    sample_raw_dir = project_root / "data" / "samples" / "raw"
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_raw_dir / "PFDA_rides.csv", raw_dir / "PFDA_rides.csv")
    shutil.copy2(sample_raw_dir / "PFDA_weather.csv", raw_dir / "PFDA_weather.csv")
    shutil.copytree(project_root / "dbt", tmp_path / "dbt")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_ingest_writes_interim_parquet_and_manifest(sample_workspace: Path) -> None:
    from ridefare.cli import main

    exit_code = main(["ingest"])

    assert exit_code == 0

    rides_path = sample_workspace / "data" / "interim" / "rides.parquet"
    weather_path = sample_workspace / "data" / "interim" / "weather.parquet"
    manifest_path = sample_workspace / "data" / "interim" / "run_manifest.json"

    assert rides_path.exists()
    assert weather_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rides_frame = pl.read_parquet(rides_path)

    assert manifest["datasets"]["rides"]["rows"] == 4
    assert manifest["datasets"]["weather"]["rows"] == 4
    assert rides_frame.columns == [
        "distance",
        "cab_type",
        "time_stamp",
        "destination",
        "source",
        "price",
        "surge_multiplier",
        "name",
    ]


def test_transform_builds_duckdb_and_marts(sample_workspace: Path) -> None:
    from ridefare.cli import main

    assert main(["ingest"]) == 0
    assert main(["transform"]) == 0

    duckdb_path = sample_workspace / "data" / "processed" / "ridefare.duckdb"
    assert duckdb_path.exists()

    conn = duckdb.connect(str(duckdb_path))
    try:
        tables = {row[0] for row in conn.execute("show tables").fetchall()}
        mart_columns = {
            row[0] for row in conn.execute("describe mart_model_features").fetchall()
        }
        mart_rows = conn.execute("select count(*) from mart_model_features").fetchone()[0]
    finally:
        conn.close()

    assert {
        "raw_rides",
        "raw_weather",
        "stg_rides",
        "stg_weather",
        "int_rides_weather_enriched",
        "fct_rides_enriched",
        "mart_pricing_dashboard",
        "mart_model_features",
    } <= tables
    assert {
        "price",
        "distance",
        "surge_multiplier",
        "cab_type",
        "temp",
        "clouds",
        "pressure",
        "rain",
        "humidity",
        "wind",
        "ride_hour",
        "ride_hour_of_day",
        "ride_day_of_week",
    } <= mart_columns
    assert mart_rows == 4
