# Deployment

## Purpose

This runbook explains RideFare's informational pull-request Preview policy and the
existing production deployment on Vercel.

## Deployment Model

- the public app lives in `apps/web`
- the public app reads static JSON artifacts from `data/processed/analytics/web` and
  `data/processed/ml/web`
- those public artifacts are versioned in git for transparency and local reproducibility
- GitHub Actions is the deploy orchestrator
- Vercel native Git auto-deploy should stay disabled so deploy behavior remains explicit

## GitHub Actions Workflows

- `ci.yml`
  runs Python validation, regenerates public artifacts in workspace, uploads the existing
  demonstration exports, and validates the frontend build against those artifacts; its
  `pull_request` and `push` declarations target `master` without path filters, including
  analytics/ML exports-only changes
- `pipeline-refresh.yml`
  regenerates public artifacts inside the runner on `master` when backend or data inputs
  change, or on manual dispatch; reports a diff summary without committing or pushing outputs
- `vercel-preview.yml`
  emits only a fixed informational notice for pull requests targeting `master` on
  `opened`, `synchronize`, and `reopened`; it does not deploy or validate the application
- `vercel-production.yml`
  builds and deploys production on `master`
- `release-please.yml`
  is configured only to manage release PRs, with a pinned action and tag/release creation
  disabled; its administrative pause remains in effect

## Required GitHub Secrets

The production Vercel workflow requires the following repository secrets:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

`vercel-preview.yml` has `permissions: {}` and no deployment credential references.
This does not revoke secrets or harden other workflows.

`pipeline-refresh.yml` uses `contents: read` and disables checkout credential persistence.
Its outputs are ephemeral runner candidates; it does not stage, commit, push, or update the
JSON versioned on `master`. The independent CI still regenerates and uploads its artifacts.
Safe publication is deferred to R2, not a restoration of the legacy push.

The local policy check is `python -I -B tests/unit/test_refresh_workflow_policy.py`.
It does not execute or validate the pipeline or the official Python 3.13 environment.

## Required Vercel Project Settings

- framework preset: `Next.js`
- Node version: `22`
- root directory: `apps/web`
- native Git auto-deploy: disabled

The app must receive `RIDEFARE_PROJECT_ROOT` at build time. The production deployment
workflow sets it to `${{ github.workspace }}` so the loaders can resolve
`data/processed/**` from the repository root during `vercel build`. Preview does not build.

## Manual Preview Checklist

1. Confirm `vercel-preview.yml` contains only `preview-policy` and the fixed notice
2. Check `ci.yml` independently; a Preview notice is not an application validation or CI pass
3. Do not expect a Preview URL or PR comment from this workflow

The notice is: "Automatic PR previews are not deployed by this workflow. This is an
informational notice, not application validation."

## Local Preview Policy Validation

From the repository root, use an interpreter with PyYAML already available:

```bash
python -I -B tests/unit/test_preview_workflow_policy.py
```

This runs `unittest` directly without pytest/conftest or RideFare module imports.
It checks the closed YAML policy, rejects unsafe in-memory candidates and duplicate keys,
and statically checks event filters. It does not execute workflow commands or contact GitHub.
The event matrix is not proof of GitHub execution, fork approval, or effective permissions/secrets.
An auxiliary Python 3.11 run validates only this YAML boundary, not the application's
`>=3.12,<3.14` environment or Linux/Python 3.13 CI, package, pipeline, or build.

PyYAML is not directly declared in `pyproject.toml`. The existing CI installs `.[data,ml,dev]`,
whose `data` extra includes `dbt-duckdb`. Published PyPI metadata for
[`dbt-duckdb 1.10.1`](https://pypi.org/pypi/dbt-duckdb/1.10.1/json) requires `dbt-core>=1.8.0`,
and [`dbt-core 1.11.7`](https://pypi.org/pypi/dbt-core/1.11.7/json) requires `pyyaml>=6.0`.
This is evidence of an existing transitive dependency, not a verified dependency resolution
or installation in Linux/Python 3.13 CI; no manifests or dependencies change in this slice.

## Scope and Authorization

The independent `ci.yml` removes only the analytics/ML `paths-ignore` filters; its jobs,
commands, and artifact flow remain unchanged. Release Please's versioned PR-only policy
is described in [Release Process](release-process.md); it neither publishes tags/releases
nor reactivates the workflow. Production deployment code and both administrative pauses
remain unchanged. Release Please still needs integrity, permission, and CI/protection
readiness checks; Production still needs promotion and credential-isolation gates.
Each reactivation requires new individual authorization. The Preview notice does not
certify global repository security.
Local preparation, publication, merge, administration, and deployment are separate permissions.
Passing the local policy test grants none of the other permissions.

Before future publication, verify workflow/ref resolution for relevant events, that the old
privileged Preview path cannot activate, data gates (CI regenerates and uploads exports),
and the other publication controls. If a safe publication bootstrap cannot be demonstrated,
any bounded Preview administrative measure needs separate authorization, verification, and
safe reversal; this slice does not pause remote workflows.

## Manual Production Checklist

1. Merge a validated pull request into `master`
2. Confirm `vercel-production.yml` finishes successfully
3. Open the production deployment and verify:
   - Home
   - Dashboard
   - `/como-funciona`
   - `Escenarios`
4. Confirm the app reads the expected artifacts without missing-state banners
5. Confirm the browser tab title and icon match the final RideFare branding
6. Confirm the shared preview metadata is present for Open Graph and Twitter cards
