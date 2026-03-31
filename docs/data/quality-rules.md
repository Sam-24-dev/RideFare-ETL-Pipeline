# Quality Rules

## Purpose

This document separates structural validation in Python from relational validation in `dbt`.

## Python Validation with Pandera

`ridefare ingest` performs structural validation before any `dbt` modeling happens.

### What Python validates

- required raw files exist
- required columns exist after header normalization
- columns can be cast into declared types
- ride rows keep all critical fields populated
- weather rows keep `location` and `time_stamp` populated
- final interim dataframes satisfy the declared `Pandera` contracts

### What Python does not validate in this phase

- business value ranges such as minimum or maximum price
- route-level consistency rules
- weather imputation quality
- advanced anomaly detection

## dbt Validation

`ridefare transform` loads raw prepared tables into `DuckDB` and then runs `dbt build`.

### What dbt validates

- `not_null` tests on key staging and mart columns
- `accepted_values` on `stg_rides.cab_type`
- singular SQL test ensuring the ride-to-weather join does not inflate row count in the fact table

## Join Stability Test

The custom SQL test compares:

- row count of `stg_rides`
- row count of `fct_rides_enriched`

Because the platform uses a left join from rides to weather, the row counts should remain equal. If the fact table has more rows, the join grain has become unstable.

## Deferred Quality Work

Later phases may add:

- richer accepted-value catalogs
- route and location conformance checks
- freshness tests
- source snapshots
- statistical anomaly checks
- ML feature drift checks
