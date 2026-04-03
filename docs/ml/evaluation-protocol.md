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

## Public Scenario Simulator

The public `/escenarios` page consumes exported artifacts from `data/processed/ml/web/`.

RideFare now supports two simulator modes:

- `model_direct`
- `hybrid_fallback`

### `model_direct`

The scenario grid is exported directly from the preprocessing pipeline plus the trained `XGBoost` regressor.

### `hybrid_fallback`

If the exported grid is degenerate for a public simulator, RideFare rebuilds the scenario grid with a bounded hybrid layer that keeps the same artifact shape while producing meaningful variation across:

- route baseline price
- time block
- weather profile
- demand level
- distance factor

The fallback is activated when the direct grid has too few unique prices or an unusably narrow span. This avoids shipping a public UI where every scenario looks identical on very small samples.

The fallback does not replace model training or champion selection. It only stabilizes the exported simulator grid for the public web product.
