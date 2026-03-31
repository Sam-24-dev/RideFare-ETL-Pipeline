# Dimensional Model

## Purpose

This document explains how raw CSV inputs become stable analytics and ML marts in the RideFare data platform.

## Layer Flow

### 1. Raw

The `raw` layer contains source CSV files:

- rides input
- weather input

These files are not queried directly by downstream consumers.

### 2. Interim

The `interim` layer stores normalized `Parquet` files produced by `ridefare ingest`:

- `rides.parquet`
- `weather.parquet`

At this layer the data has:

- normalized headers
- explicit types
- duplicate row removal
- conservative null dropping for critical fields

### 3. Staging

The `staging` layer is modeled in `dbt`:

- `stg_rides`
- `stg_weather`

Staging exposes:

- row identifiers
- normalized timestamps
- hourly time buckets
- canonical business columns

### 4. Intermediate

The `intermediate` layer contains the operational join:

- `int_rides_weather_enriched`

Join grain:

- `source = location`
- `ride_hour = weather_hour`

The join is a left join from rides to weather to preserve ride coverage.

### 5. Marts

The current platform exposes these marts:

- `fct_rides_enriched`
  - row-level fact table after the legacy join
- `mart_pricing_dashboard`
  - aggregated cuts for dashboard KPIs and business analysis
- `mart_model_features`
  - stable feature-target table for the future ML workflow

## Fact and Feature Grain

### `fct_rides_enriched`

One row per ride after enrichment with weather columns for the matched source and hour.

### `mart_pricing_dashboard`

One row per:

- `ride_date`
- `ride_hour`
- `source`
- `destination`
- `cab_type`

### `mart_model_features`

One row per enriched ride, with:

- target: `price`
- numeric features: `distance`, `surge_multiplier`, weather metrics
- categorical features: `source`, `destination`, `cab_type`, `ride_name`
- temporal features: `ride_hour`, `ride_hour_of_day`, `ride_day_of_week`

## Notes

- This phase preserves the legacy hourly join semantics for stability.
- More advanced dimensional modeling can happen later if the business story requires route or trip dimensions beyond the current scope.
