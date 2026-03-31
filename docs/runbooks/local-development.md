# Local Development

## Purpose

This runbook describes the expected developer setup after the `ML System` phase.

## Prerequisites

- Python 3.13
- Node.js 22+
- Corepack available through Node.js

## Bootstrap

### Python

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

### Frontend workspace

```powershell
corepack pnpm install
```

## Validation

### Python

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-python.ps1
```

### Frontend

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-web.ps1
```

## Notes

- The Python runtime is pinned to 3.13 because the current `dbt` toolchain is not stable on Python 3.14 in this repository
- `scripts/bootstrap.ps1` creates `.venv` and installs `.[data,ml,dev]`
- `ridefare ingest` expects raw files at `data/raw/PFDA_rides.csv` and `data/raw/PFDA_weather.csv` unless CLI overrides are provided
- `ridefare transform` expects `data/interim/rides.parquet` and `data/interim/weather.parquet`
- `ridefare train` expects `mart_model_features` to exist in the local DuckDB warehouse
- `ridefare export-web` reads the latest successful ML run by default
- The public UI language will be Spanish, but technical docs remain in English
