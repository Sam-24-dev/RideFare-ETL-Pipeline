"""Frontend export flow for RideFare ML artifacts."""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from ridefare.config import ExportWebConfig
from ridefare.exceptions import ExportArtifactsError
from ridefare.serialization import make_json_safe, write_json


@dataclass(frozen=True)
class ExportWebResult:
    """Output path for a successful web export."""

    selected_run_dir: Path
    web_output_dir: Path


def run_export_web(config: ExportWebConfig) -> ExportWebResult:
    """Convert a completed train run into frontend-ready JSON artifacts."""

    run_dir = config.selected_run_dir
    if not run_dir.exists():
        raise ExportArtifactsError(
            f"Missing ML run artifacts at {run_dir}. Run train first or provide --run-id."
        )

    required_paths = {
        "run_manifest": run_dir / "run_manifest.json",
        "metrics": run_dir / "metrics.json",
        "comparison": run_dir / "comparison.json",
        "feature_importance": run_dir / "feature_importance.json",
        "shap_summary": run_dir / "shap_summary.json",
        "predictions": run_dir / "predictions.parquet",
    }
    missing = [name for name, path in required_paths.items() if not path.exists()]
    if missing:
        raise ExportArtifactsError(
            f"Missing run artifacts for web export: {', '.join(sorted(missing))}"
        )

    run_manifest = read_json(required_paths["run_manifest"])
    metrics = read_json(required_paths["metrics"])
    comparison = read_json(required_paths["comparison"])
    feature_importance = read_json(required_paths["feature_importance"])
    shap_summary = read_json(required_paths["shap_summary"])
    predictions = pl.read_parquet(required_paths["predictions"]).sort(
        ["model_name", "ride_hour", "ride_id"]
    )

    champion_model = comparison["champion_model"]
    champion_predictions = predictions.filter(pl.col("model_name") == champion_model)

    overview = {
        "run_id": run_manifest["run_id"],
        "generated_at": run_manifest["generated_at"],
        "champion_model": champion_model,
        "explainability_model": run_manifest["explainability_model"],
        "row_count": run_manifest["dataset"]["row_count"],
        "time_range": run_manifest["dataset"]["time_range"],
        "feature_columns": run_manifest["dataset"]["feature_columns"],
        "holdout_rows": run_manifest["split_plan"]["holdout_rows"],
        "development_rows": run_manifest["split_plan"]["development_rows"],
    }
    model_metrics = [
        {
            "model_name": model_entry["model_name"],
            "holdout": metrics["models"][model_entry["model_name"]]["holdout"],
            "cross_validation": metrics["models"][model_entry["model_name"]]["cross_validation"][
                "summary"
            ],
        }
        for model_entry in comparison["models"]
    ]

    config.web_output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".tmp-web-",
        dir=str(config.web_output_dir.parent),
    ) as temp_dir_name:
        temp_web_dir = Path(temp_dir_name)
        write_json(temp_web_dir / "model_overview.json", overview)
        write_json(temp_web_dir / "model_metrics.json", model_metrics)
        write_json(temp_web_dir / "feature_importance.json", feature_importance["features"])
        write_json(temp_web_dir / "shap_summary.json", shap_summary)
        write_json(
            temp_web_dir / "prediction_snapshot.json",
            champion_predictions.head(50).to_dicts(),
        )
        write_json(temp_web_dir / "run_manifest.json", run_manifest)

        if config.web_output_dir.exists():
            shutil.rmtree(config.web_output_dir)
        shutil.move(str(temp_web_dir), str(config.web_output_dir))

    return ExportWebResult(
        selected_run_dir=run_dir,
        web_output_dir=config.web_output_dir,
    )


def read_json(path: Path) -> dict[str, object]:
    """Read JSON and normalize values into plain Python types."""

    return make_json_safe(json.loads(path.read_text(encoding="utf-8")))
