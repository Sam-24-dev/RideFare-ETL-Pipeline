"""Frontend export flow for RideFare analytics and ML artifacts."""

from __future__ import annotations

import json
import pickle
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mode

import duckdb
import numpy as np
import pandas as pd
import polars as pl
from xgboost import XGBRegressor

from ridefare.config import ExportWebConfig
from ridefare.exceptions import ExportArtifactsError, MissingArtifactError
from ridefare.serialization import make_json_safe, write_json

DASHBOARD_SOURCE_QUERY = """
select
  ride_date,
  ride_hour,
  source,
  destination,
  cab_type,
  total_rides,
  avg_price,
  min_price,
  max_price,
  avg_distance,
  avg_surge_multiplier,
  avg_temp,
  avg_clouds,
  avg_humidity
from mart_pricing_dashboard
order by ride_hour, source, destination, cab_type
"""

TIME_BLOCKS = (
    {"id": "madrugada", "label": "Madrugada", "hours": [0, 1, 2, 3, 4, 5], "anchor_hour": 3},
    {"id": "manana", "label": "Mañana", "hours": [6, 7, 8, 9, 10, 11], "anchor_hour": 9},
    {"id": "tarde", "label": "Tarde", "hours": [12, 13, 14, 15, 16, 17], "anchor_hour": 15},
    {"id": "noche", "label": "Noche", "hours": [18, 19, 20, 21, 22, 23], "anchor_hour": 21},
)

DISTANCE_FACTORS = (
    {"id": "compacta", "label": "Compacta", "factor": 0.85},
    {"id": "referencia", "label": "Referencia", "factor": 1.0},
    {"id": "extendida", "label": "Extendida", "factor": 1.15},
)


@dataclass(frozen=True)
class ExportWebResult:
    """Output paths for a successful web export."""

    selected_run_dir: Path
    web_output_dir: Path
    analytics_output_dir: Path


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
        "dataset_snapshot": run_dir / "dataset_snapshot.parquet",
        "xgboost_model": run_dir / "models" / "xgboost_regressor.json",
        "xgboost_preprocessor": run_dir / "models" / "xgboost_preprocessor.pkl",
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
    dataset_snapshot = pd.DataFrame(
        pl.read_parquet(required_paths["dataset_snapshot"]).to_dicts()
    )
    dashboard_frame = load_dashboard_frame(config.duckdb_path)

    champion_model = str(comparison["champion_model"])
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
    scenario_payload = build_scenario_payload(
        dataset_snapshot=dataset_snapshot,
        metrics=metrics,
        model_path=required_paths["xgboost_model"],
        preprocessor_path=required_paths["xgboost_preprocessor"],
    )
    dashboard_payloads = build_dashboard_payloads(dashboard_frame)

    config.web_output_dir.parent.mkdir(parents=True, exist_ok=True)
    config.analytics_output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".tmp-web-",
        dir=str(config.web_output_dir.parent),
    ) as temp_web_dir_name, tempfile.TemporaryDirectory(
        prefix=".tmp-analytics-",
        dir=str(config.analytics_output_dir.parent),
    ) as temp_analytics_dir_name:
        temp_web_dir = Path(temp_web_dir_name)
        temp_analytics_dir = Path(temp_analytics_dir_name)

        write_json(temp_web_dir / "model_overview.json", overview)
        write_json(temp_web_dir / "model_metrics.json", model_metrics)
        write_json(temp_web_dir / "feature_importance.json", feature_importance["features"])
        write_json(temp_web_dir / "shap_summary.json", shap_summary)
        write_json(
            temp_web_dir / "prediction_snapshot.json",
            champion_predictions.head(50).to_dicts(),
        )
        write_json(temp_web_dir / "run_manifest.json", run_manifest)
        write_json(temp_web_dir / "scenario_controls.json", scenario_payload["controls"])
        write_json(temp_web_dir / "scenario_grid.json", scenario_payload["grid"])

        for file_name, payload in dashboard_payloads.items():
            write_json(temp_analytics_dir / file_name, payload)

        if config.web_output_dir.exists():
            shutil.rmtree(config.web_output_dir)
        shutil.move(str(temp_web_dir), str(config.web_output_dir))

        if config.analytics_output_dir.exists():
            shutil.rmtree(config.analytics_output_dir)
        shutil.move(str(temp_analytics_dir), str(config.analytics_output_dir))

    return ExportWebResult(
        selected_run_dir=run_dir,
        web_output_dir=config.web_output_dir,
        analytics_output_dir=config.analytics_output_dir,
    )


def load_dashboard_frame(duckdb_path: Path) -> pd.DataFrame:
    """Load the analytics mart used by the public dashboard."""

    if not duckdb_path.exists():
        raise MissingArtifactError(f"Missing DuckDB database: {duckdb_path}")

    conn = duckdb.connect(str(duckdb_path))
    try:
        tables = {row[0] for row in conn.execute("show tables").fetchall()}
        if "mart_pricing_dashboard" not in tables:
            raise MissingArtifactError(
                f"Missing analytics dataset 'mart_pricing_dashboard' in {duckdb_path}"
            )
        frame = conn.execute(DASHBOARD_SOURCE_QUERY).fetch_df()
    finally:
        conn.close()

    if frame.empty:
        raise ExportArtifactsError(
            "The analytics mart is empty; dashboard exports cannot be built."
        )

    frame["ride_hour"] = pd.to_datetime(frame["ride_hour"], utc=False)
    frame["ride_date"] = pd.to_datetime(frame["ride_date"], utc=False)
    return frame


def build_dashboard_payloads(frame: pd.DataFrame) -> dict[str, object]:
    """Generate stable frontend JSON payloads for the analytics dashboard."""

    total_rides = int(frame["total_rides"].sum())
    weighted_avg_price = weighted_average(frame["avg_price"], frame["total_rides"])
    weighted_avg_surge = weighted_average(frame["avg_surge_multiplier"], frame["total_rides"])
    dominant_route = (
        frame.groupby(["source", "destination"], as_index=False)["total_rides"]
        .sum()
        .sort_values(["total_rides", "source", "destination"], ascending=[False, True, True])
        .iloc[0]
    )
    time_min = frame["ride_hour"].min()
    time_max = frame["ride_hour"].max()

    overview = {
        "generated_at": datetime.now(tz=UTC),
        "time_range": {
            "min": None if pd.isna(time_min) else time_min.isoformat(),
            "max": None if pd.isna(time_max) else time_max.isoformat(),
        },
        "dimensions": {
            "sources": int(frame["source"].nunique()),
            "destinations": int(frame["destination"].nunique()),
            "cab_types": int(frame["cab_type"].nunique()),
        },
        "kpis": [
            {
                "id": "total_rides",
                "label": "Viajes modelados",
                "value": total_rides,
                "format": "integer",
            },
            {
                "id": "avg_price",
                "label": "Tarifa media",
                "value": weighted_avg_price,
                "format": "currency",
            },
            {
                "id": "avg_surge_multiplier",
                "label": "Surge medio",
                "value": weighted_avg_surge,
                "format": "multiplier",
            },
            {
                "id": "dominant_route",
                "label": "Ruta más activa",
                "value": f"{dominant_route['source']} → {dominant_route['destination']}",
                "format": "text",
            },
        ],
    }

    timeseries = frame.loc[
        :,
        [
            "ride_date",
            "ride_hour",
            "source",
            "destination",
            "cab_type",
            "total_rides",
            "avg_price",
            "avg_surge_multiplier",
        ],
    ].sort_values(["ride_hour", "source", "destination", "cab_type"])

    route_breakdown = (
        frame.groupby(["source", "destination", "cab_type"], as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "total_rides": int(group["total_rides"].sum()),
                    "avg_price": weighted_average(group["avg_price"], group["total_rides"]),
                    "avg_distance": weighted_average(group["avg_distance"], group["total_rides"]),
                    "avg_surge_multiplier": weighted_average(
                        group["avg_surge_multiplier"], group["total_rides"]
                    ),
                }
            ),
            include_groups=False,
        )
        .sort_values(
            ["total_rides", "avg_price", "source", "destination", "cab_type"],
            ascending=[False, False, True, True, True],
        )
        .head(24)
    )

    weather_impact = frame.loc[
        :,
        [
            "ride_date",
            "ride_hour",
            "source",
            "destination",
            "cab_type",
            "total_rides",
            "avg_price",
            "avg_temp",
            "avg_clouds",
            "avg_humidity",
        ],
    ].sort_values(["ride_hour", "source", "destination", "cab_type"])

    filter_payload = {
        "sources": sorted(frame["source"].dropna().unique().tolist()),
        "destinations": sorted(frame["destination"].dropna().unique().tolist()),
        "cab_types": sorted(frame["cab_type"].dropna().unique().tolist()),
        "time_windows": list(TIME_BLOCKS),
    }

    return {
        "dashboard_overview.json": overview,
        "dashboard_timeseries.json": timeseries.to_dict(orient="records"),
        "dashboard_route_breakdown.json": route_breakdown.to_dict(orient="records"),
        "dashboard_weather_impact.json": weather_impact.to_dict(orient="records"),
        "dashboard_filters.json": filter_payload,
    }


def build_scenario_payload(
    *,
    dataset_snapshot: pd.DataFrame,
    metrics: dict[str, object],
    model_path: Path,
    preprocessor_path: Path,
) -> dict[str, object]:
    """Generate a precomputed scenario grid for the public simulator."""

    if dataset_snapshot.empty:
        raise ExportArtifactsError(
            "The dataset snapshot is empty; simulator artifacts cannot exist."
        )

    dataset_snapshot["ride_hour"] = pd.to_datetime(dataset_snapshot["ride_hour"], utc=False)
    xgboost_metrics = metrics["models"]["xgboost"]["holdout"]
    model_rmse = float(xgboost_metrics["rmse"])

    with preprocessor_path.open("rb") as file_handle:
        preprocessor = pickle.load(file_handle)

    estimator = XGBRegressor()
    estimator.load_model(model_path)

    route_catalog = build_route_catalog(dataset_snapshot)
    weather_profiles = build_weather_profiles(dataset_snapshot)
    surge_levels = build_surge_levels(dataset_snapshot)
    default_day_of_week = most_common_int(dataset_snapshot["ride_day_of_week"].dropna())

    grid_rows: list[dict[str, object]] = []
    for route in route_catalog:
        for time_block in TIME_BLOCKS:
            for weather_profile in weather_profiles:
                for surge_multiplier in surge_levels:
                    for distance_option in DISTANCE_FACTORS:
                        prediction_frame = pd.DataFrame(
                            [
                                {
                                    "distance": max(
                                        float(route["median_distance"])
                                        * float(distance_option["factor"]),
                                        0.1,
                                    ),
                                    "surge_multiplier": surge_multiplier,
                                    "temp": weather_profile["values"]["temp"],
                                    "clouds": weather_profile["values"]["clouds"],
                                    "pressure": weather_profile["values"]["pressure"],
                                    "rain": weather_profile["values"]["rain"],
                                    "humidity": weather_profile["values"]["humidity"],
                                    "wind": weather_profile["values"]["wind"],
                                    "ride_hour_of_day": time_block["anchor_hour"],
                                    "ride_day_of_week": default_day_of_week,
                                    "source": route["source"],
                                    "destination": route["destination"],
                                    "cab_type": route["cab_type"],
                                    "ride_name": route["ride_name"],
                                }
                            ]
                        )
                        transformed = np.asarray(preprocessor.transform(prediction_frame))
                        predicted_price = float(estimator.predict(transformed)[0])
                        grid_rows.append(
                            {
                                "source": route["source"],
                                "destination": route["destination"],
                                "cab_type": route["cab_type"],
                                "ride_name": route["ride_name"],
                                "route_distance_median": route["median_distance"],
                                "time_block": time_block["id"],
                                "weather_profile": weather_profile["id"],
                                "surge_multiplier": surge_multiplier,
                                "distance_factor": distance_option["factor"],
                                "predicted_price": predicted_price,
                                "price_band_low": max(predicted_price - model_rmse, 0.0),
                                "price_band_high": predicted_price + model_rmse,
                            }
                        )

    destinations_by_source: dict[str, list[str]] = {}
    for route in route_catalog:
        destinations = destinations_by_source.setdefault(str(route["source"]), [])
        if route["destination"] not in destinations:
            destinations.append(str(route["destination"]))
    for destinations in destinations_by_source.values():
        destinations.sort()

    controls = {
        "generated_at": datetime.now(tz=UTC),
        "model_name": "xgboost",
        "default_day_of_week": default_day_of_week,
        "sources": sorted(destinations_by_source),
        "destinations_by_source": destinations_by_source,
        "cab_types": sorted({str(route["cab_type"]) for route in route_catalog}),
        "time_blocks": list(TIME_BLOCKS),
        "weather_profiles": weather_profiles,
        "surge_levels": surge_levels,
        "distance_factors": list(DISTANCE_FACTORS),
        "route_catalog": route_catalog,
    }
    return {"controls": controls, "grid": grid_rows}


def build_route_catalog(dataset_snapshot: pd.DataFrame) -> list[dict[str, object]]:
    """Return a bounded set of representative routes for the simulator."""

    grouped = (
        dataset_snapshot.groupby(["source", "destination", "cab_type"], as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "ride_name": most_common_text(group["ride_name"]),
                    "median_distance": float(group["distance"].median()),
                    "total_rides": int(group["ride_id"].count()),
                }
            ),
            include_groups=False,
        )
        .sort_values(
            ["total_rides", "median_distance", "source", "destination", "cab_type"],
            ascending=[False, True, True, True, True],
        )
        .head(24)
    )
    return grouped.to_dict(orient="records")


def build_weather_profiles(dataset_snapshot: pd.DataFrame) -> list[dict[str, object]]:
    """Derive bounded weather profiles from the modeled dataset."""

    numeric = dataset_snapshot.loc[:, ["temp", "clouds", "pressure", "rain", "humidity", "wind"]]
    median = numeric.median(numeric_only=True)
    q25 = numeric.quantile(0.25, numeric_only=True)
    q75 = numeric.quantile(0.75, numeric_only=True)

    def payload_from(values: pd.Series) -> dict[str, float]:
        return {column: float(values[column]) for column in numeric.columns}

    return [
        {
            "id": "despejado",
            "label": "Despejado",
            "description": "Menos nubosidad y humedad, con lluvia casi nula.",
            "values": payload_from(
                pd.Series(
                    {
                        "temp": median["temp"],
                        "clouds": q25["clouds"],
                        "pressure": median["pressure"],
                        "rain": q25["rain"],
                        "humidity": q25["humidity"],
                        "wind": median["wind"],
                    }
                )
            ),
        },
        {
            "id": "nublado",
            "label": "Nublado",
            "description": (
                "Cobertura de nubes alta, con el resto de condiciones cercanas al promedio."
            ),
            "values": payload_from(
                pd.Series(
                    {
                        "temp": median["temp"],
                        "clouds": q75["clouds"],
                        "pressure": median["pressure"],
                        "rain": median["rain"],
                        "humidity": median["humidity"],
                        "wind": median["wind"],
                    }
                )
            ),
        },
        {
            "id": "lluvia",
            "label": "Lluvia",
            "description": "Mayor intensidad de lluvia y humedad.",
            "values": payload_from(
                pd.Series(
                    {
                        "temp": q25["temp"],
                        "clouds": q75["clouds"],
                        "pressure": median["pressure"],
                        "rain": q75["rain"],
                        "humidity": q75["humidity"],
                        "wind": median["wind"],
                    }
                )
            ),
        },
        {
            "id": "ventoso",
            "label": "Ventoso",
            "description": "Condiciones con mayor intensidad de viento.",
            "values": payload_from(
                pd.Series(
                    {
                        "temp": median["temp"],
                        "clouds": median["clouds"],
                        "pressure": median["pressure"],
                        "rain": median["rain"],
                        "humidity": median["humidity"],
                        "wind": q75["wind"],
                    }
                )
            ),
        },
    ]


def build_surge_levels(dataset_snapshot: pd.DataFrame) -> list[float]:
    """Return a bounded set of surge levels grounded in the observed data."""

    observed = sorted(
        {
            round(float(value), 2)
            for value in dataset_snapshot["surge_multiplier"].dropna().tolist()
            if float(value) > 0
        }
    )
    if not observed:
        return [1.0]
    if len(observed) <= 5:
        return observed

    quantiles = (
        dataset_snapshot["surge_multiplier"]
        .dropna()
        .quantile([0.0, 0.25, 0.5, 0.75, 1.0])
        .round(2)
        .tolist()
    )
    return sorted({float(value) for value in quantiles if float(value) > 0})


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    """Compute a weighted mean using only finite values."""

    if values.empty:
        return 0.0
    return float(np.average(values.astype(float), weights=weights.astype(float)))


def most_common_int(series: pd.Series) -> int:
    """Return the most common integer value in a series."""

    values = [int(value) for value in series.tolist()]
    return mode(values) if values else 0


def most_common_text(series: pd.Series) -> str:
    """Return the most common text value in a series."""

    values = [str(value) for value in series.tolist() if pd.notna(value)]
    return mode(values) if values else "Servicio"


def read_json(path: Path) -> dict[str, object]:
    """Read JSON and normalize values into plain Python types."""

    return make_json_safe(json.loads(path.read_text(encoding="utf-8")))
