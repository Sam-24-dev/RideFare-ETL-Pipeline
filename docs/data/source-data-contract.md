# Source Data Contract

## Purpose

This document defines the expected raw inputs for the RideFare data platform during `Phase 2: Data Platform`.

## Expected Raw Files

### Rides

- Default location: `data/raw/PFDA_rides.csv`
- Required columns:
  - `distance`
  - `cab_type`
  - `time_stamp`
  - `destination`
  - `source`
  - `price`
  - `surge_multiplier`
  - `name`

### Weather

- Default location: `data/raw/PFDA_weather.csv`
- Required columns:
  - `temp`
  - `clouds`
  - `pressure`
  - `rain`
  - `humidity`
  - `wind`
  - `location`
  - `time_stamp`

## Header Normalization

Raw headers are normalized before validation:

- leading and trailing whitespace is removed
- non-alphanumeric separators are converted to `_`
- headers are lowercased

Example:

- ` Ride Name ` becomes `ride_name`
- `Surge Multiplier` becomes `surge_multiplier`

## Timestamp Semantics

Legacy timestamp units are preserved in the platform:

- rides `time_stamp`: Unix epoch in milliseconds
- weather `time_stamp`: Unix epoch in seconds

These assumptions are required for the hourly join strategy inherited from the legacy notebook.

## Null Handling

### Rides

Rows are dropped if any required ride field is null after type casting.

### Weather

Rows are dropped only when `location` or `time_stamp` are null.

Weather measurements such as `temp`, `rain`, or `humidity` may remain null in this phase. No imputation is performed during ingestion.

## Failure Modes

`ridefare ingest` fails explicitly when:

- a required raw file is missing
- a required column is missing
- values cannot be cast into the declared contract and produce invalid nulls in critical fields
- the resulting dataframe violates the `Pandera` contract

## Stable Interim Outputs

Successful ingestion produces:

- `data/interim/rides.parquet`
- `data/interim/weather.parquet`
- `data/interim/run_manifest.json`

The run manifest records row counts, detected columns, and the execution timestamp.
