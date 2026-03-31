from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_default_paths_include_ml_artifact_locations() -> None:
    from ridefare.config import RideFarePaths

    project_root = (Path("tmp") / "ridefare").resolve()

    paths = RideFarePaths.defaults(project_root=project_root)
    train_config = paths.train_config(run_id="unit-run")
    export_config = paths.export_web_config(run_id="unit-run")

    assert train_config.artifacts_dir == project_root / "data" / "processed" / "ml"
    assert train_config.run_dir == train_config.artifacts_dir / "runs" / "unit-run"
    assert export_config.web_output_dir == train_config.artifacts_dir / "web"
    assert export_config.selected_run_dir == train_config.run_dir


def test_export_web_config_treats_latest_as_the_latest_directory() -> None:
    from ridefare.config import RideFarePaths

    project_root = (Path("tmp") / "ridefare").resolve()

    paths = RideFarePaths.defaults(project_root=project_root)
    export_config = paths.export_web_config(run_id="latest")

    assert export_config.run_id == "latest"
    assert export_config.selected_run_dir == project_root / "data" / "processed" / "ml" / "latest"


def test_build_split_plan_uses_fallback_for_small_sample() -> None:
    from ridefare.ml_training import build_split_plan

    plan = build_split_plan(row_count=4)

    assert plan.holdout_rows == 1
    assert plan.development_rows == 3
    assert plan.cv_splits_used == 2
    assert plan.validation_rows == 1


def test_build_split_plan_keeps_temporal_order_without_leakage() -> None:
    from ridefare.ml_training import build_split_plan

    plan = build_split_plan(row_count=15)

    assert plan.holdout_start_index == 12
    assert plan.development_rows == 12
    assert plan.holdout_rows == 3
    assert plan.cv_splits_used == 4


def test_build_modeling_dataset_rejects_missing_required_columns() -> None:
    from ridefare.exceptions import ModelingDataError
    from ridefare.ml_dataset import build_modeling_dataset

    frame = pd.DataFrame(
        {
            "ride_id": [1],
            "ride_hour": ["2024-03-31T12:00:00"],
            "source": ["North End"],
            "destination": ["Back Bay"],
            "cab_type": ["Uber"],
            "distance": [2.1],
            "surge_multiplier": [1.0],
            "price": [12.5],
            "ride_hour_of_day": [12],
            "ride_day_of_week": [0],
        }
    )

    with pytest.raises(ModelingDataError, match="ride_name"):
        build_modeling_dataset(frame)


def test_make_json_safe_converts_numpy_scalars_and_non_finite_values() -> None:
    from ridefare.serialization import make_json_safe

    payload = {
        "value": np.float64(1.25),
        "missing": np.nan,
        "nested": [np.int64(4), np.float32(2.5)],
    }

    safe_payload = make_json_safe(payload)

    assert safe_payload["value"] == 1.25
    assert safe_payload["missing"] is None
    assert safe_payload["nested"] == [4, 2.5]
