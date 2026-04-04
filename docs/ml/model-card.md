# Model Card

## Problem Framing

RideFare estimates ride price using historical trip context and weather conditions.

The current model is designed for:

- portfolio-grade experimentation
- comparative offline evaluation
- frontend storytelling artifacts

It is not designed for production fare setting, dispatch optimization, or rider-facing guarantees.

## Target

- target column: `price`
- source mart: `mart_model_features`

## Feature Groups

### Numeric

- `distance`
- `surge_multiplier`
- `temp`
- `clouds`
- `pressure`
- `rain`
- `humidity`
- `wind`
- `ride_hour_of_day`
- `ride_day_of_week`

### Categorical

- `source`
- `destination`
- `cab_type`
- `ride_name`

## Training Data Source

The ML workflow reads the modeled feature mart from the local `DuckDB` warehouse.

Upstream lineage:

- raw CSV inputs
- `ridefare ingest`
- `ridefare transform`
- `dbt build`
- `mart_model_features`

## Model Set

The workflow trains four regressors:

- `DummyRegressor`
- `LinearRegression`
- `RandomForestRegressor`
- `XGBRegressor`

`XGBoost` is the primary model and the source for explainability artifacts.

## Evaluation Summary

Evaluation is temporal rather than random.

Reported metrics:

- `MAE`
- `RMSE`
- `R2`

The champion model is selected by lowest holdout `RMSE`, with deterministic tie-breaking.

## Limitations

- the current feature space is intentionally conservative and uses only the modeled mart
- weather joins are still based on the preserved hourly legacy logic
- small sample runs can downgrade cross-validation depth to keep the workflow executable
- the exported JSON artifacts are for visualization, not online inference

## Likely Failure Cases

- unseen or sparse route combinations
- extreme surge or weather conditions not well represented in history
- short-term operational shocks that are not captured by hourly weather joins
- business regime changes that alter price formation

## Responsible Use Note

This project estimates observed historical prices. It should not be presented as a source of guaranteed future fares, fairness claims, or rider-level decision support without additional validation and governance.

## Public Product Surface

RideFare exposes the ML layer to the public app through exported artifacts rather than a live
inference API.

- `/dashboard` consumes analytics artifacts for descriptive pricing stories
- `/escenarios` consumes ML-oriented exports for the public scenario simulator
- when the direct exported scenario grid is too flat for a public reading, the simulator can fall
  back to the bounded hybrid export mode documented in `docs/ml/evaluation-protocol.md`
