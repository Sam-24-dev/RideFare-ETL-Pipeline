# RideFare

RideFare is being rebuilt as a portfolio-grade data product that combines analytics
engineering, machine learning, and product-focused frontend delivery.

Phases `1` through `4` are implemented on the supported Python `3.13` toolchain.
`Deployment and Automation` plus final portfolio polish remain after this branch.

## Project Direction

- Public UI: Spanish
- Technical documentation: English
- Data stack: `Polars`, `DuckDB`, `dbt`, `Pandera`
- ML stack: `scikit-learn`, `XGBoost`, `SHAP`
- Frontend stack: `Next.js`, `TypeScript`, `Tailwind CSS`, `shadcn/ui`, `Framer Motion`, `Apache ECharts`
- Deployment target: `Vercel`

## Current Status

The legacy assets have been preserved as references while the new platform is being built:

- Legacy notebook: [notebooks/ridefare_analysis_engineering_legacy.ipynb](./notebooks/ridefare_analysis_engineering_legacy.ipynb)
- Legacy ETL script: [scripts/legacy/etl_db_legacy.py](./scripts/legacy/etl_db_legacy.py)
- Legacy audit: [docs/architecture/legacy-audit.md](./docs/architecture/legacy-audit.md)

## Data Platform Deliverables

- `ridefare ingest` command that validates raw CSV inputs and writes clean `Parquet` outputs
- `ridefare transform` command that loads prepared raw tables into `DuckDB` and runs `dbt build`
- `dbt` models for `staging`, `intermediate`, and `marts`
- Versioned sample raw inputs under `data/samples/raw`
- Data contracts and quality rules documented in `docs/data/`

## ML System Deliverables

- `ridefare train` command that reads `mart_model_features` and writes versioned ML runs
- baseline models with deterministic comparison against the primary `XGBoost` model
- temporal evaluation outputs, holdout predictions, feature importance, and SHAP artifacts
- `ridefare export-web` command that writes frontend-ready JSON files under
  `data/processed/ml/web` and `data/processed/analytics/web`
- model documentation in `docs/ml/`

## Web Product Deliverables

- Spanish public routes for `/`, `/dashboard`, `/como-funciona`, and `/escenarios`
- typed frontend data loaders backed by exported JSON artifacts and runtime `zod` validation
- editorial analytics dashboard with ECharts visualizations and client-side filters
- public `/como-funciona` page that translates pipeline and ML decisions into portfolio-ready copy
- public `/escenarios` page driven by exported artifacts and a scenario simulator
- `Escenarios` formally replaces the earlier `Model lab` concept as the public predictive surface
- visual system documented in `docs/ui/design-system.md`

## Python Compatibility

- The supported local runtime is `Python 3.13`
- `pyproject.toml` is pinned to `>=3.12,<3.14`
- `dbt` in this repository is not stable on Python `3.14`, so local pipeline validation must run inside the `3.13` virtual environment created by `scripts/bootstrap.ps1`
- On Windows, prefer `scripts/validate-python.ps1` or `.\.venv\Scripts\python.exe -m pytest`; a bare `pytest` command may still resolve to a global Python `3.14` installation

## Working Agreement

- The notebook is not the source of truth
- Production logic must live in Python, SQL/dbt, and TypeScript
- Public UI stays in Spanish while technical documentation stays in English

## Local Development

Detailed local setup lives in [docs/runbooks/local-development.md](./docs/runbooks/local-development.md).
