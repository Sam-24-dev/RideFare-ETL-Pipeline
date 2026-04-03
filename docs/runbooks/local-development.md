# Local Development

## Purpose

This runbook describes the expected developer setup after the `Web Product` phase.

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

### Generate sample public artifacts

```powershell
.\.venv\Scripts\python -m ridefare ingest --rides-path data/samples/raw/PFDA_rides.csv --weather-path data/samples/raw/PFDA_weather.csv
.\.venv\Scripts\python -m ridefare transform
.\.venv\Scripts\python -m ridefare train --run-id local-web
.\.venv\Scripts\python -m ridefare export-web --run-id local-web
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

- The Python runtime is pinned to `3.13` because the current `dbt` toolchain is not stable on Python `3.14` in this repository
- If `ridefare transform` fails with a `mashumaro` or `dbt` import error, confirm that `.venv\Scripts\python --version` reports `3.13.x`
- Prefer `powershell -ExecutionPolicy Bypass -File .\scripts\validate-python.ps1` or `.\.venv\Scripts\python.exe -m pytest`; a bare `pytest` command may still resolve to a global Python `3.14` interpreter on Windows
- `scripts/bootstrap.ps1` creates `.venv` and installs `.[data,ml,dev]`
- `ridefare ingest` expects raw files at `data/raw/PFDA_rides.csv` and `data/raw/PFDA_weather.csv` unless CLI overrides are provided
- `ridefare transform` expects `data/interim/rides.parquet` and `data/interim/weather.parquet`
- `ridefare train` expects `mart_model_features` to exist in the local DuckDB warehouse
- `ridefare export-web` reads the latest successful ML run by default
- `ridefare export-web` now also writes dashboard artifacts under `data/processed/analytics/web`
- The public app reads generated JSON from the filesystem; it does not call an API at runtime
- The public UI language will be Spanish, but technical docs remain in English
