# Modeling Strategy

## Purpose

The modeling layer is intended to show disciplined ML workflow design rather than maximum leaderboard performance.

## Strategy

The project uses a staged modeling approach:

1. naive baseline with `DummyRegressor`
2. interpretable baseline with `LinearRegression`
3. legacy-aligned tree baseline with `RandomForestRegressor`
4. primary model with `XGBoost`

This keeps the workflow explainable and makes every reported gain defensible.

## Why This Stack

- `scikit-learn` provides stable preprocessing and baseline interfaces
- `RandomForest` preserves continuity with the original notebook direction
- `XGBoost` is a strong tabular model with a mature sklearn API
- `SHAP` provides explainability outputs that can be reused by the frontend

## Explicit Non-Goals for This Phase

- online inference API
- automated hyperparameter search service
- MLflow deployment
- model serving infrastructure
- drift monitoring in production

## Output Contract

Every successful train run must produce:

- comparable metrics across models
- row-level holdout predictions
- feature importance
- SHAP outputs
- stable JSON exports for the web product

The goal is a repeatable offline ML system that integrates cleanly with the current analytics platform.
