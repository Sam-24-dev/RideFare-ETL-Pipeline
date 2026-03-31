# ADR 0001: Monorepo Structure

## Status

Accepted

## Context

The original repository stored the ETL script, notebook, and documentation at the root level. That layout was sufficient for an exploratory project, but it does not scale to a layered data product with analytics, ML, and frontend delivery.

## Decision

Adopt a monorepo-style structure with clear boundaries:

- `apps/web` for the public web application
- `src/ridefare` for Python production code
- `dbt` for analytical transformations
- `docs` for technical documentation
- `tests` for verification

Legacy assets are preserved outside the canonical production paths.

## Consequences

### Positive

- clearer separation of concerns
- easier onboarding
- safer growth across multiple subsystems
- more credible portfolio structure

### Negative

- higher upfront setup cost
- more directories and tooling from day one

## Alternatives Considered

- Keep the flat root-level layout
- Split into separate repositories for data and web

The flat layout was rejected because it reinforces notebook-centered development. Separate repositories were rejected because the project should remain a single portfolio artifact.
