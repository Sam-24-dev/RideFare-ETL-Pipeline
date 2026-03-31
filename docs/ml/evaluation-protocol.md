# Evaluation Protocol

## Why Random Split Was Rejected

The legacy notebook used a random split. That approach leaks future information into training and overstates performance for a time-ordered pricing problem.

RideFare now uses a deterministic temporal evaluation workflow.

## Temporal Split Logic

1. Order the modeled dataset by `ride_hour`, then `ride_id`
2. Reserve the latest `20%` of rows as final holdout
3. Use the earliest `80%` as the development window
4. Run `TimeSeriesSplit` on the development window for model comparison
5. Reserve the latest `10%` of the development window as the XGBoost validation window for early stopping

For very small datasets, the workflow reduces the number of CV splits while preserving chronology.

## Model Set

- `dummy_mean`
- `linear_regression`
- `random_forest`
- `xgboost`

## Metrics

The workflow reports:

- `MAE`
- `RMSE`
- `R2`

Champion selection is based on holdout `RMSE`.

## Artifact Versioning

Each train run writes a versioned directory under:

- `data/processed/ml/runs/<run_id>/`

The latest successful run is mirrored to:

- `data/processed/ml/latest/`

Frontend-oriented exports are written to:

- `data/processed/ml/web/`

## Explainability

Explainability artifacts are generated from the primary `XGBoost` model so the frontend contract stays stable across runs.

Outputs include:

- feature importance
- SHAP global importance
- bounded sample-level SHAP records
- PNG plots for inspection
