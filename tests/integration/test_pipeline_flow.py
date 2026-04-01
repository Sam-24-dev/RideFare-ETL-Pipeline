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


def test_train_and_export_web_produce_ml_artifacts(sample_workspace: Path) -> None:
    from ridefare.cli import main

    assert main(["ingest"]) == 0
    assert main(["transform"]) == 0
    assert main(["train", "--run-id", "sample-ml-run"]) == 0
    assert main(["export-web", "--run-id", "sample-ml-run"]) == 0

    ml_root = sample_workspace / "data" / "processed" / "ml"
    analytics_web_dir = sample_workspace / "data" / "processed" / "analytics" / "web"
    run_dir = ml_root / "runs" / "sample-ml-run"
    latest_dir = ml_root / "latest"
    web_dir = ml_root / "web"

    assert (run_dir / "dataset_snapshot.parquet").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "comparison.json").exists()
    assert (run_dir / "predictions.parquet").exists()
    assert (run_dir / "feature_importance.json").exists()
    assert (run_dir / "shap_summary.json").exists()
    assert (run_dir / "models").exists()
    assert (run_dir / "plots").exists()
    assert latest_dir.exists()
    assert web_dir.exists()
    assert analytics_web_dir.exists()

    comparison = json.loads((run_dir / "comparison.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    web_overview = json.loads((web_dir / "model_overview.json").read_text(encoding="utf-8"))
    scenario_controls = json.loads((web_dir / "scenario_controls.json").read_text(encoding="utf-8"))
    scenario_grid = json.loads((web_dir / "scenario_grid.json").read_text(encoding="utf-8"))
    dashboard_overview = json.loads(
        (analytics_web_dir / "dashboard_overview.json").read_text(encoding="utf-8")
    )

    assert comparison["champion_model"] in {
        "dummy_mean",
        "linear_regression",
        "random_forest",
        "xgboost",
    }
    assert metrics["models"]
    assert web_overview["champion_model"] == comparison["champion_model"]
    assert scenario_controls["sources"]
    assert scenario_controls["weather_profiles"]
    assert scenario_grid
    assert dashboard_overview["kpis"]
