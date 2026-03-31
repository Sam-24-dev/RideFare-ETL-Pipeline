# Legacy Audit

## Goal

Record which legacy assets are preserved, rewritten, or retired during the `Foundation` phase.

## Asset Decisions

| Asset | Decision | Rationale | Current Location |
| --- | --- | --- | --- |
| Original ETL script | rewrite as production module | The current script proves the ETL concept but is too limited for the new architecture | `scripts/legacy/etl_db_legacy.py` |
| Original notebook | keep as legacy reference | The notebook contains baseline metrics, SQL join logic, feature ideas, and early analysis context | `notebooks/ridefare_analysis_engineering_legacy.ipynb` |
| Original README | discard and replace | The previous README described the old architecture and would misrepresent the current direction | `README.md` replaced in root |
| Feature importance image | keep as historical reference | The image is useful as a legacy ML artifact and as evidence of the original baseline work | `docs/ui/assets/feature-importance-legacy.png` |

## Preserved Inputs

- ETL concept based on ride and weather CSV ingestion
- Join strategy between rides and weather by timestamp and location
- Baseline modeling direction using price prediction
- Initial observed metrics around RMSE and R²

## Not Canonical Anymore

- Root-level ETL script
- Root-level notebook workflow
- SQLite-centered project narrative
- Notebook-first execution model

## Foundation Outcome

The legacy project is preserved for traceability, but future implementation must happen in the canonical codebase under `src/ridefare`, `dbt`, and `apps/web`.
