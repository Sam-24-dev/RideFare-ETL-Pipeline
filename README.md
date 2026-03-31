# RideFare

RideFare is being rebuilt as a portfolio-grade data product that combines analytics engineering, machine learning, and product-focused frontend delivery.

The repository has completed the `Foundation` phase and is currently in `Data Platform`.

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

## Working Agreement

- `AGENTS.md` is the operational guide for every implementation iteration
- `ROADMAP.md` is the phase guide for the full project
- The notebook is not the source of truth
- Production logic must live in Python, SQL/dbt, and TypeScript

## Local Development

Detailed local setup lives in [docs/runbooks/local-development.md](./docs/runbooks/local-development.md).
