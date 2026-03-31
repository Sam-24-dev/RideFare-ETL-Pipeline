# ADR 0002: Foundation Stack

## Status

Accepted

## Context

The project needs a stack that supports data work, ML workflows, and a production-grade frontend without overengineering the first implementation phase.

## Decision

Approve the following stack for the foundation:

- Python package tooling through `pyproject.toml`
- data and analytics stack: `Polars`, `DuckDB`, `dbt`, `Pandera`
- ML stack: `scikit-learn`, `XGBoost`, `SHAP`
- web stack: `Next.js`, `TypeScript`, `Tailwind CSS`
- validation tooling: `pytest`, `Ruff`
- deployment target: `Vercel`

During `Foundation`, only the minimal package, command surface, and web shell are created.

## Consequences

### Positive

- aligned with the long-term roadmap
- avoids re-platforming in later phases
- supports all three target profile narratives

### Negative

- setup complexity is higher than the original repo
- some dependencies remain placeholders until later phases

## Alternatives Considered

- Keep `pandas` + `SQLite` as the permanent core
- Build a Streamlit-first app
- Add orchestration and cloud services immediately

These alternatives were rejected because they would either undercut the target architecture or increase complexity too early.
