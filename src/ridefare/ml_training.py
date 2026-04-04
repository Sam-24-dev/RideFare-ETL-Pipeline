"""Repeatable ML workflow for RideFare pricing models."""

from __future__ import annotations

import math
import pickle
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import shap
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from ridefare.config import TrainConfig
from ridefare.exceptions import ModelingDataError, TrainingPipelineError
from ridefare.ml_contracts import ModelingDataset
from ridefare.ml_dataset import build_modeling_dataset, load_modeling_frame
from ridefare.serialization import write_json

MODEL_PRIORITY = {
    "xgboost": 0,
    "random_forest": 1,
    "linear_regression": 2,
    "dummy_mean": 3,
}


@dataclass(frozen=True)
class SplitPlan:
    total_rows: int
    holdout_rows: int
    development_rows: int
    holdout_start_index: int
    cv_splits_requested: int
    cv_splits_used: int
    validation_rows: int


@dataclass(frozen=True)
class TrainResult:
    run_id: str
    run_dir: Path
    latest_dir: Path
    comparison_path: Path
    metrics_path: Path


@dataclass(frozen=True)
class ModelOutcome:
    model_name: str
    holdout_metrics: dict[str, float]
    cv_folds: list[dict[str, float | int]]
    cv_summary: dict[str, float]
    predictions: pd.DataFrame
    feature_names: list[str]
    sklearn_pipeline: Pipeline | None = None
    preprocessor: ColumnTransformer | None = None
    estimator: object | None = None
    transformed_holdout: np.ndarray | None = None


def build_split_plan(row_count: int) -> SplitPlan:
    """Build a temporal split plan with a safe fallback for tiny samples."""

    if row_count < 4:
        raise ModelingDataError("At least 4 modeled rows are required for temporal training.")

    holdout_rows = max(1, math.ceil(row_count * 0.2))
    while row_count - holdout_rows < 3 and holdout_rows > 1:
        holdout_rows -= 1

    development_rows = row_count - holdout_rows
    if development_rows < 3:
        raise ModelingDataError(
            "The modeled dataset is too small to create development and holdout windows."
        )

    cv_splits_requested = 4
    cv_splits_used = min(cv_splits_requested, development_rows - 1)
    if cv_splits_used < 2:
        raise ModelingDataError("At least 2 temporal CV splits are required.")

    validation_rows = max(1, math.ceil(development_rows * 0.1))
    if development_rows - validation_rows < 2:
        validation_rows = 1

    return SplitPlan(
        total_rows=row_count,
        holdout_rows=holdout_rows,
        development_rows=development_rows,
        holdout_start_index=development_rows,
        cv_splits_requested=cv_splits_requested,
        cv_splits_used=cv_splits_used,
        validation_rows=validation_rows,
    )


def run_train(config: TrainConfig) -> TrainResult:
    """Execute the full ML workflow and materialize versioned artifacts."""

    dataset = build_modeling_dataset(load_modeling_frame(config.duckdb_path))
    split_plan = build_split_plan(dataset.metadata.row_count)

    config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".tmp-{config.run_id}-",
        dir=str(config.artifacts_dir),
    ) as temp_dir_name:
        temp_run_dir = Path(temp_dir_name)
        plots_dir = temp_run_dir / "plots"
        models_dir = temp_run_dir / "models"
        plots_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        write_dataset_snapshot(dataset, temp_run_dir / "dataset_snapshot.parquet")

        model_outcomes = [
            train_baseline_model(
                "dummy_mean",
                dataset,
                split_plan,
                DummyRegressor(strategy="mean"),
            ),
            train_baseline_model(
                "linear_regression",
                dataset,
                split_plan,
                LinearRegression(),
            ),
            train_baseline_model(
                "random_forest",
                dataset,
                split_plan,
                RandomForestRegressor(n_estimators=300, n_jobs=-1, random_state=42),
            ),
        ]
        xgboost_outcome = train_xgboost_model(dataset, split_plan)
        model_outcomes.append(xgboost_outcome)

        comparison = build_comparison_payload(model_outcomes)
        champion = next(
            outcome
            for outcome in model_outcomes
            if outcome.model_name == comparison["champion_model"]
        )
        feature_importance = build_feature_importance_payload(xgboost_outcome)
        shap_summary = build_shap_payload(xgboost_outcome, dataset, split_plan)
        metrics_payload = build_metrics_payload(dataset, split_plan, model_outcomes, comparison)
        run_manifest = build_run_manifest(config, dataset, split_plan, comparison)

        predictions_frame = pd.concat(
            [outcome.predictions for outcome in model_outcomes],
            ignore_index=True,
        )
        write_predictions(predictions_frame, temp_run_dir / "predictions.parquet")
        save_models(model_outcomes, models_dir)

        write_json(temp_run_dir / "comparison.json", comparison)
        write_json(temp_run_dir / "metrics.json", metrics_payload)
        write_json(temp_run_dir / "run_manifest.json", run_manifest)
        write_json(temp_run_dir / "feature_importance.json", feature_importance)
        write_json(temp_run_dir / "shap_summary.json", shap_summary)

        create_metrics_comparison_plot(model_outcomes, plots_dir / "metrics_comparison.png")
        create_actual_vs_predicted_plot(champion, plots_dir / "actual_vs_predicted.png")
        create_residual_distribution_plot(champion, plots_dir / "residual_distribution.png")
        create_shap_summary_plot(shap_summary["global_importance"], plots_dir / "shap_summary.png")

        finalize_run_artifacts(temp_run_dir, config)

    return TrainResult(
        run_id=config.run_id,
        run_dir=config.run_dir,
        latest_dir=config.latest_dir,
        comparison_path=config.run_dir / "comparison.json",
        metrics_path=config.run_dir / "metrics.json",
    )


def make_preprocessor(dataset: ModelingDataset) -> ColumnTransformer:
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, list(dataset.contract.numeric_features)),
            ("categorical", categorical_pipeline, list(dataset.contract.categorical_features)),
        ]
    )


def train_baseline_model(
    model_name: str,
    dataset: ModelingDataset,
    split_plan: SplitPlan,
    estimator,
) -> ModelOutcome:
    development_features = dataset.features.iloc[: split_plan.development_rows]
    development_target = dataset.target.iloc[: split_plan.development_rows]
    holdout_features = dataset.features.iloc[split_plan.holdout_start_index :]
    holdout_target = dataset.target.iloc[split_plan.holdout_start_index :]
    holdout_context = dataset.frame.iloc[split_plan.holdout_start_index :].reset_index(drop=True)

    cv_folds: list[dict[str, float | int]] = []
    for fold_index, (train_index, validation_index) in enumerate(
        TimeSeriesSplit(n_splits=split_plan.cv_splits_used).split(development_features),
        start=1,
    ):
        fold_pipeline = Pipeline(
            [
                ("preprocessor", make_preprocessor(dataset)),
                ("model", estimator.__class__(**estimator.get_params())),
            ]
        )
        X_train = development_features.iloc[train_index]
        y_train = development_target.iloc[train_index]
        X_validation = development_features.iloc[validation_index]
        y_validation = development_target.iloc[validation_index]
        fold_pipeline.fit(X_train, y_train)
        cv_folds.append(
            {
                "fold": fold_index,
                **calculate_metrics(y_validation.to_numpy(), fold_pipeline.predict(X_validation)),
            }
        )

    final_pipeline = Pipeline([("preprocessor", make_preprocessor(dataset)), ("model", estimator)])
    final_pipeline.fit(development_features, development_target)
    holdout_predictions = final_pipeline.predict(holdout_features)

    return ModelOutcome(
        model_name=model_name,
        holdout_metrics=calculate_metrics(holdout_target.to_numpy(), holdout_predictions),
        cv_folds=cv_folds,
        cv_summary=summarize_cv_results(cv_folds),
        predictions=build_predictions_frame(holdout_context, holdout_predictions, model_name),
        feature_names=final_pipeline.named_steps["preprocessor"].get_feature_names_out().tolist(),
        sklearn_pipeline=final_pipeline,
    )


def train_xgboost_model(dataset: ModelingDataset, split_plan: SplitPlan) -> ModelOutcome:
    development_features = dataset.features.iloc[: split_plan.development_rows]
    development_target = dataset.target.iloc[: split_plan.development_rows]
    holdout_features = dataset.features.iloc[split_plan.holdout_start_index :]
    holdout_target = dataset.target.iloc[split_plan.holdout_start_index :]
    holdout_context = dataset.frame.iloc[split_plan.holdout_start_index :].reset_index(drop=True)

    cv_folds: list[dict[str, float | int]] = []
    for fold_index, (train_index, validation_index) in enumerate(
        TimeSeriesSplit(n_splits=split_plan.cv_splits_used).split(development_features),
        start=1,
    ):
        preprocessor = make_preprocessor(dataset)
        X_train = preprocessor.fit_transform(development_features.iloc[train_index])
        X_validation = preprocessor.transform(development_features.iloc[validation_index])
        y_train = development_target.iloc[train_index]
        y_validation = development_target.iloc[validation_index]
        estimator = make_xgboost_estimator(use_early_stopping=False)
        estimator.fit(X_train, y_train, verbose=False)
        cv_folds.append(
            {
                "fold": fold_index,
                **calculate_metrics(y_validation.to_numpy(), estimator.predict(X_validation)),
            }
        )

    training_rows = split_plan.development_rows - split_plan.validation_rows
    if training_rows < 2:
        raise TrainingPipelineError("The development window is too small for XGBoost validation.")

    X_train_frame = development_features.iloc[:training_rows]
    y_train = development_target.iloc[:training_rows]
    X_validation_frame = development_features.iloc[training_rows : split_plan.development_rows]
    y_validation = development_target.iloc[training_rows : split_plan.development_rows]

    preprocessor = make_preprocessor(dataset)
    X_train = preprocessor.fit_transform(X_train_frame)
    X_validation = preprocessor.transform(X_validation_frame)
    X_holdout = np.asarray(preprocessor.transform(holdout_features))

    estimator = make_xgboost_estimator(use_early_stopping=True)
    estimator.fit(X_train, y_train, eval_set=[(X_validation, y_validation)], verbose=False)
    holdout_predictions = estimator.predict(X_holdout)

    return ModelOutcome(
        model_name="xgboost",
        holdout_metrics=calculate_metrics(holdout_target.to_numpy(), holdout_predictions),
        cv_folds=cv_folds,
        cv_summary=summarize_cv_results(cv_folds),
        predictions=build_predictions_frame(holdout_context, holdout_predictions, "xgboost"),
        feature_names=preprocessor.get_feature_names_out().tolist(),
        preprocessor=preprocessor,
        estimator=estimator,
        transformed_holdout=X_holdout,
    )


def make_xgboost_estimator(*, use_early_stopping: bool) -> XGBRegressor:
    params = dict(
        objective="reg:squarederror",
        eval_metric="rmse",
        tree_method="hist",
        n_estimators=400,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=42,
    )
    if use_early_stopping:
        params["early_stopping_rounds"] = 25
    return XGBRegressor(**params)


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    r2 = 0.0 if len(actual) < 2 else float(r2_score(actual, predicted))
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(math.sqrt(mean_squared_error(actual, predicted))),
        "r2": r2,
    }


def summarize_cv_results(cv_folds: list[dict[str, float | int]]) -> dict[str, float]:
    if not cv_folds:
        raise TrainingPipelineError("At least one CV fold is required.")
    return {
        metric: float(np.mean([float(fold[metric]) for fold in cv_folds]))
        for metric in ("mae", "rmse", "r2")
    }


def build_predictions_frame(
    holdout_context: pd.DataFrame,
    holdout_predictions: np.ndarray,
    model_name: str,
) -> pd.DataFrame:
    frame = holdout_context.loc[
        :,
        [
            "ride_id",
            "ride_hour",
            "source",
            "destination",
            "cab_type",
            "ride_name",
            "distance",
            "surge_multiplier",
            "price",
        ],
    ].copy()
    frame = frame.rename(columns={"price": "actual"})
    frame["predicted"] = holdout_predictions
    frame["residual"] = frame["actual"] - frame["predicted"]
    frame["model_name"] = model_name
    return frame


def build_comparison_payload(model_outcomes: list[ModelOutcome]) -> dict[str, object]:
    model_summaries = [
        {
            "model_name": outcome.model_name,
            "holdout": outcome.holdout_metrics,
            "cross_validation": outcome.cv_summary,
        }
        for outcome in model_outcomes
    ]
    ranked_models = sorted(
        model_summaries,
        key=lambda summary: (
            float(summary["holdout"]["rmse"]),
            MODEL_PRIORITY[summary["model_name"]],
        ),
    )
    return {
        "champion_model": ranked_models[0]["model_name"],
        "models": ranked_models,
    }


def build_metrics_payload(
    dataset: ModelingDataset,
    split_plan: SplitPlan,
    model_outcomes: list[ModelOutcome],
    comparison: dict[str, object],
) -> dict[str, object]:
    return {
        "generated_at": datetime.now(tz=UTC),
        "dataset": {
            "row_count": dataset.metadata.row_count,
            "fingerprint": dataset.metadata.fingerprint,
            "time_range": dataset.metadata.time_range,
        },
        "split_plan": {
            "development_rows": split_plan.development_rows,
            "holdout_rows": split_plan.holdout_rows,
            "cv_splits_requested": split_plan.cv_splits_requested,
            "cv_splits_used": split_plan.cv_splits_used,
            "validation_rows": split_plan.validation_rows,
        },
        "champion_model": comparison["champion_model"],
        "models": {
            outcome.model_name: {
                "holdout": outcome.holdout_metrics,
                "cross_validation": {
                    "folds": outcome.cv_folds,
                    "summary": outcome.cv_summary,
                },
            }
            for outcome in model_outcomes
        },
    }


def build_run_manifest(
    config: TrainConfig,
    dataset: ModelingDataset,
    split_plan: SplitPlan,
    comparison: dict[str, object],
) -> dict[str, object]:
    return {
        "run_id": config.run_id,
        "generated_at": datetime.now(tz=UTC),
        "source": {
            "duckdb_path": _public_source_path(
                config.duckdb_path,
                project_root=config.project_root,
            ),
            "model_source": "mart_model_features",
            "dataset_fingerprint": dataset.metadata.fingerprint,
        },
        "dataset": {
            "row_count": dataset.metadata.row_count,
            "null_counts": dataset.metadata.null_counts,
            "time_range": dataset.metadata.time_range,
            "feature_columns": dataset.metadata.feature_columns,
        },
        "split_plan": {
            "holdout_rows": split_plan.holdout_rows,
            "development_rows": split_plan.development_rows,
            "cv_splits_requested": split_plan.cv_splits_requested,
            "cv_splits_used": split_plan.cv_splits_used,
            "validation_rows": split_plan.validation_rows,
        },
        "champion_model": comparison["champion_model"],
        "explainability_model": "xgboost",
    }


def _public_source_path(path: Path, *, project_root: Path) -> str:
    """Normalize local paths before exporting public-facing artifacts."""

    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def build_feature_importance_payload(xgboost_outcome: ModelOutcome) -> dict[str, object]:
    if xgboost_outcome.estimator is None:
        raise TrainingPipelineError("XGBoost estimator is required for feature importance export.")

    importances = getattr(xgboost_outcome.estimator, "feature_importances_", None)
    if importances is None:
        raise TrainingPipelineError("XGBoost did not expose feature importances.")

    features = [
        {"feature": feature_name, "importance": float(importance)}
        for feature_name, importance in zip(
            xgboost_outcome.feature_names,
            importances,
            strict=True,
        )
    ]
    return {
        "model_name": xgboost_outcome.model_name,
        "features": sorted(features, key=lambda item: item["importance"], reverse=True),
    }


def build_shap_payload(
    xgboost_outcome: ModelOutcome,
    dataset: ModelingDataset,
    split_plan: SplitPlan,
) -> dict[str, object]:
    if xgboost_outcome.estimator is None or xgboost_outcome.transformed_holdout is None:
        raise TrainingPipelineError("XGBoost outcome is incomplete for SHAP generation.")

    transformed_holdout = np.asarray(xgboost_outcome.transformed_holdout)
    if transformed_holdout.size == 0:
        raise TrainingPipelineError("SHAP generation requires at least one holdout row.")

    explainer = shap.Explainer(xgboost_outcome.estimator)
    shap_values = explainer(transformed_holdout)
    values = np.asarray(shap_values.values)
    global_scores = np.mean(np.abs(values), axis=0)
    global_importance = sorted(
        [
            {"feature": feature_name, "mean_abs_shap": float(score)}
            for feature_name, score in zip(
                xgboost_outcome.feature_names,
                global_scores,
                strict=True,
            )
        ],
        key=lambda item: item["mean_abs_shap"],
        reverse=True,
    )

    holdout_context = dataset.frame.iloc[split_plan.holdout_start_index :].reset_index(drop=True)
    samples = []
    for row_index in range(min(len(holdout_context), 10)):
        contributions = sorted(
            [
                {
                    "feature": feature_name,
                    "shap_value": float(values[row_index, feature_index]),
                }
                for feature_index, feature_name in enumerate(xgboost_outcome.feature_names)
            ],
            key=lambda item: abs(item["shap_value"]),
            reverse=True,
        )[:5]
        samples.append(
            {
                "ride_id": int(holdout_context.iloc[row_index]["ride_id"]),
                "ride_hour": holdout_context.iloc[row_index]["ride_hour"],
                "base_value": float(np.ravel(shap_values.base_values)[row_index]),
                "top_contributions": contributions,
            }
        )

    return {
        "model_name": xgboost_outcome.model_name,
        "global_importance": global_importance,
        "samples": samples,
    }


def write_dataset_snapshot(dataset: ModelingDataset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(dataset.frame.to_dict(orient="list")).write_parquet(path)


def write_predictions(predictions: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(predictions.to_dict(orient="list")).write_parquet(path)


def save_models(model_outcomes: list[ModelOutcome], models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    for outcome in model_outcomes:
        if outcome.model_name == "xgboost":
            if outcome.estimator is None or outcome.preprocessor is None:
                raise TrainingPipelineError("XGBoost outcome is incomplete for model export.")
            outcome.estimator.get_booster().save_model(models_dir / "xgboost_regressor.json")
            with (models_dir / "xgboost_preprocessor.pkl").open("wb") as file_handle:
                pickle.dump(outcome.preprocessor, file_handle)
            continue

        if outcome.sklearn_pipeline is None:
            raise TrainingPipelineError(f"Missing pipeline export for model: {outcome.model_name}")
        with (models_dir / f"{outcome.model_name}.pkl").open("wb") as file_handle:
            pickle.dump(outcome.sklearn_pipeline, file_handle)


def create_metrics_comparison_plot(model_outcomes: list[ModelOutcome], path: Path) -> None:
    model_names = [outcome.model_name for outcome in model_outcomes]
    fig, axes = plt.subplots(ncols=3, figsize=(14, 4))
    for axis, metric in zip(axes, ("mae", "rmse", "r2"), strict=True):
        axis.bar(model_names, [outcome.holdout_metrics[metric] for outcome in model_outcomes])
        axis.set_title(metric.upper())
        axis.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def create_actual_vs_predicted_plot(outcome: ModelOutcome, path: Path) -> None:
    fig, axis = plt.subplots(figsize=(6, 5))
    axis.scatter(outcome.predictions["actual"], outcome.predictions["predicted"])
    axis.set_xlabel("Actual price")
    axis.set_ylabel("Predicted price")
    axis.set_title(f"Actual vs predicted ({outcome.model_name})")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def create_residual_distribution_plot(outcome: ModelOutcome, path: Path) -> None:
    fig, axis = plt.subplots(figsize=(6, 4))
    axis.hist(outcome.predictions["residual"], bins=min(10, len(outcome.predictions)))
    axis.set_xlabel("Residual")
    axis.set_ylabel("Count")
    axis.set_title(f"Residual distribution ({outcome.model_name})")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def create_shap_summary_plot(global_importance: list[dict[str, float]], path: Path) -> None:
    top_features = global_importance[:10]
    fig, axis = plt.subplots(figsize=(8, 5))
    axis.barh(
        [item["feature"] for item in reversed(top_features)],
        [item["mean_abs_shap"] for item in reversed(top_features)],
    )
    axis.set_xlabel("Mean |SHAP value|")
    axis.set_title("SHAP summary")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def finalize_run_artifacts(temp_run_dir: Path, config: TrainConfig) -> None:
    runs_dir = config.artifacts_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    if config.run_dir.exists():
        shutil.rmtree(config.run_dir)
    shutil.move(str(temp_run_dir), str(config.run_dir))

    if config.latest_dir.exists():
        shutil.rmtree(config.latest_dir)
    shutil.copytree(config.run_dir, config.latest_dir)
