# ADR 0003: Versioned Public Artifacts and Actions-Driven Deploys

## Status

Accepted

## Context

RideFare serves a static public frontend from `apps/web`, but that frontend depends on
generated analytics and ML artifacts under `data/processed/**`. During `Web Product`,
those files were created locally and consumed directly by the app. For `Deployment and
Automation`, the project needs a deploy story that is reproducible, reviewable, and
does not depend on manual local refresh steps.

## Decision

Adopt the following delivery model:

- version only the public artifact subsets under:
  - `data/processed/analytics/web/**`
  - `data/processed/ml/web/**`
- generate those artifacts through a single script:
  `scripts/refresh-public-artifacts.ps1`
- use GitHub Actions as the orchestration layer for:
  - CI
  - artifact refresh
  - Vercel preview deploys
  - Vercel production deploys
  - release automation
- disable Vercel native Git auto-deploy so deployment behavior remains explicit and
  traceable through repository workflows

## Consequences

### Positive

- the public data contract is visible in git
- previews and production deploys can rebuild from a known workflow
- the repository tells a clearer end-to-end story for portfolio reviewers
- local development and CI share the same refresh flow

### Negative

- public artifact JSON files now add noise to git history
- a refresh workflow must avoid commit loops and deploy confusion
- Vercel configuration requires repository secrets and one-time project setup

## Alternatives Considered

- keep all processed artifacts ignored and regenerate only in local environments
- let Vercel Git integration deploy automatically without GitHub Actions control
- add a live inference or backend API for the frontend

These alternatives were rejected because they either hide the delivery chain, reduce
reviewability, or add infrastructure that is outside the first full portfolio build.
