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
  declares only a manual, CI-gated preparation/build on `master`, without Vercel credentials,
  publication, or bundle transfer; its administrative pause remains in effect
- `release-please.yml`
  is configured only to manage release PRs, with a pinned action and tag/release creation
  disabled; its administrative pause remains in effect

## Existing Deployment Credentials — Not Used by the Build Boundary

The build-only workflow does not reference Vercel secrets. The existing repository secrets
are not revoked, relocated, or modified by this code change:

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

The app must receive `RIDEFARE_PROJECT_ROOT` at build time. The build-only workflow sets it
to `${{ github.workspace }}` so the loaders can resolve `data/processed/**` from the repository
root during `vercel build`. Preview does not build.

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
nor reactivates the workflow. R0-PR2F-A replaces Production's legacy deployment steps with a
manual build boundary; both administrative pauses remain unchanged. Release Please still
needs its separate recovery checks and is outside this unit. Production's hosted build
experiment and any later publisher, promotion, or credential relocation remain separate gates.
Each reactivation requires new individual authorization. The Preview notice does not
certify global repository security.
Local preparation, publication, merge, administration, and deployment are separate permissions.
Passing the local policy test grants none of the other permissions.

Before future publication, verify workflow/ref resolution for relevant events, that the old
privileged Preview path cannot activate, data gates (CI regenerates and uploads exports),
and the other publication controls. If a safe publication bootstrap cannot be demonstrated,
any bounded Preview administrative measure needs separate authorization, verification, and
safe reversal; this slice does not pause remote workflows.

## R0-PR2F-A — Manual Build Boundary, Not Deployment

Production and Release Please remain administratively paused. Do not enable or dispatch
this workflow without new, separate authorization for a hosted experiment. Local preparation,
publication, or integration of this code does not grant that authorization.

The declaration accepts only `workflow_dispatch`, with explicit `ci_run_id` and
`ci_run_attempt` string inputs. Before checkout or project code, the runner's isolated
Python interpreter performs GitHub GETs and rejects a foreign repository, a non-`master`
ref, or a SHA different from current remote `master`. It requires CI workflow `256052140`,
`push/master`, the exact SHA, `completed/success`, and the requested attempt. Both
`python-quality` and `web-quality` must be successful jobs of that attempt, with successful
checks from GitHub Actions App `15368` in the same check suite. Missing, unexpected, or
incomplete jobs and failed API reads stop the build. The latest CI attempt and master are
rechecked before emitting the immutable checkout SHA; these GETs are not globally atomic.

Checkout uses that validated SHA and `persist-credentials:false`. GitHub permissions are
limited to `contents:read`, `actions:read`, and `checks:read`; the API token is scoped to
the gate step. This is a boundary without **Vercel** credentials, not a claim that no
GitHub token exists. Existing pins, Python 3.13, Node 22, pnpm installation, Vercel CLI
50.39.0, and runner-side regeneration are retained. Regeneration and the Vercel bundle
are new build outputs, not the artifact previously built or validated by CI.

### Public settings and fail-closed behavior

The workflow materializes only `.vercel/project.json` from public project metadata
observed by GET on 2026-10-16: project `ride-fare-etl-pipeline-web`, repository
`Sam-24-dev/RideFare-ETL-Pipeline`, framework `nextjs`, root `apps/web`, Node `22.x`,
null command/output overrides, and the observed creation time and directory-listing flag.
Its settings shape and tokenless build path were inspected in the official CLI
[`50.39.0` source](https://github.com/vercel/vercel/tree/26539cfdb2971a9c40f1fb7cd22a152b92161164/packages/cli/src).
IDs come from metadata, not secret values. No settings are fetched during the build;
future project-setting changes require fresh metadata review, not guessed defaults.

Preparation rejects an existing `.vercel` directory or global-config directory, then
creates a fresh, empty CLI global-config directory. Immediately before `vercel build --prod`,
a SHA-256 check requires the exact settings file; a missing or changed file fails.
There is no `--yes`, authentication token, pull/link/login fallback, environment-file download,
authentication-cache reuse, deployment, promotion, upload, or later publisher in this workflow.
The independent CI retains its existing demonstration-export uploads.

### Validation and remaining unknowns

Run only the static policy locally with `python -I -B tests/unit/test_production_workflow_policy.py`.
It parses the real YAML and exercises its CI gate with in-memory GitHub responses and mocked
GET/output interfaces; it never runs application commands, installs tools, or invokes Vercel.

A passing policy is **not a demonstrated credentialless build**. A separately authorized
hosted experiment must establish CLI/Next.js compatibility with the recorded settings,
any required non-secret build inputs, generated-data resolution, output completeness and
runtime paths, and actual execution/permissions of the CI gate. This unit neither transfers
nor certifies a portable bundle, byte-for-byte equality with CI output, or deployment safety.
No Environment configuration, credential migration, or publication is included. The existing
Production deployment and the `git.deploymentEnabled:false` setting must remain unchanged.
