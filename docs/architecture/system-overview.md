# System Overview

## Purpose

RideFare is being rebuilt as a layered data product rather than a notebook demo.

The target system combines:

- a reproducible data pipeline
- a documented ML workflow
- a public web product for storytelling and exploration

## Layers

### 1. Data ingestion and contracts

Raw ride and weather data will be ingested through Python modules under `src/ridefare`, validated with `Pandera`, and normalized before entering the analytics layer.

### 2. Analytical modeling

Cleaned datasets will be stored in `Parquet` and queried with `DuckDB`. `dbt` will model the warehouse into `staging`, `intermediate`, and `marts` layers.

### 3. Machine learning

The ML layer will consume modeled datasets, train baseline and primary models, and export explainability and evaluation artifacts.

### 4. Web product

The public-facing application will consume static exports and present the project through a Spanish-language interface built with `Next.js`.

## Current Scope

The current phase implements the first operational data platform slice:

- raw rides and weather CSV ingestion
- `Pandera` contracts for input validation
- clean `Parquet` outputs in `data/interim`
- a local `DuckDB` warehouse file in `data/processed`
- `dbt` marts for dashboard-ready and model-ready consumption

The ML workflow and the public web product remain future phases.
