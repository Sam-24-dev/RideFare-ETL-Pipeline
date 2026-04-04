# System Overview

## Purpose

RideFare is a finished hybrid portfolio project that combines:

- a reproducible analytics pipeline
- a documented ML workflow
- a deployed public web experience in Spanish

The repository is no longer a notebook-centered demo. The operational system now lives in
Python, `dbt`, and TypeScript.

## Runtime Surfaces

### Data and warehouse

- `ridefare ingest` validates and normalizes raw ride and weather inputs
- `ridefare transform` writes modeled tables into the local `DuckDB` warehouse and runs
  `dbt build`
- analytics and ML marts are exposed from the same reproducible warehouse path under
  `data/processed/ridefare.duckdb`

### Machine learning

- `ridefare train` reads `mart_model_features` and writes versioned ML runs under
  `data/processed/ml/runs/<run_id>/`
- the workflow exports holdout predictions, comparison metrics, feature importance, and SHAP
  artifacts
- `ridefare export-web` translates the latest run and the analytics mart into frontend-ready
  JSON files

### Public web product

The public app in `apps/web` consumes static artifacts and exposes four routes:

- `/`
- `/dashboard`
- `/como-funciona`
- `/escenarios`

`Escenarios` is the public predictive surface and replaces the earlier `Model lab` concept.

### Delivery

- GitHub Actions validates Python and frontend paths
- GitHub Actions refreshes versioned public artifacts
- GitHub Actions orchestrates preview and production deploys
- Vercel hosts the public application

## System Flow

1. Sample or raw CSV inputs enter the repo through `ridefare ingest`
2. Cleaned outputs move into `Parquet`, `DuckDB`, and `dbt` marts through `ridefare transform`
3. `ridefare train` creates explainable ML artifacts from `mart_model_features`
4. `ridefare export-web` produces versioned public JSON subsets for analytics and scenarios
5. The Next.js app renders the public experience from those artifacts
6. GitHub Actions and Vercel deliver the final product

## Repository State

The current repository includes all roadmap phases from Foundation through Deployment and
Automation. Phase 6 exists to polish presentation, tighten narrative consistency, and make the
repo read like a deliberate portfolio product from README to browser tab.
