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
  declares a manual, CI-gated build on `master` and a same-run, credentialless transfer
  verifier on a second runner; it has no publisher and its administrative pause remains in effect
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
needs its separate recovery checks and is outside this unit. The separately authorized
2F-A run `38847785133` demonstrated one credentialless hosted build on
`531b7c696226ebfb2c299ef07982840036cc098c`; its pause was restored and it has zero artifacts.
B1 adds only a transfer candidate, not a publisher. A transfer experiment, promotion,
credential relocation, and any publication remain separately authorized gates.
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
authentication-cache reuse, deployment, promotion, or later publisher. B1 adds only the
bounded output upload/verification described below; independent CI keeps its existing
separate demonstration-export uploads.

### Validation and remaining unknowns

Run only the static policy locally with `python -I -B tests/unit/test_production_workflow_policy.py`.
It parses the real YAML and exercises its CI gate with in-memory GitHub responses and mocked
GET/output interfaces; it never runs application commands, installs tools, or invokes Vercel.

A passing local policy alone is **not a demonstrated credentialless hosted build**.
The separate 2F-A experiment verified gate execution with read-only GitHub permissions,
exact checkout, regeneration, and `vercel build` for that one run. It did not retain an
artifact, establish the full output topology/size, or test transfer and operational portability.
B1's local fixtures do not close those gaps. No Environment configuration, credential migration,
or publication is included. Existing Production and `git.deploymentEnabled:false` stay unchanged.

## R0-PR2F-B1 — Verified Transfer Candidate, No Publisher

This declaration is not permission to enable or dispatch Production. Production `256058391`
and Release Please `256058390` must remain `disabled_manually` until individual authorization.
The accepted 2F-A experiment must not be rerun to stand in for a future transfer experiment.

### Exact scope and package

The producer retains the exact CI gate, first eleven steps, pins, Python 3.13, Node 22,
Vercel CLI 50.39.0, public settings hash, and runner-side regeneration. After its build,
a standard-library Python script inventories **only** `.vercel/output`. It writes one
uncompressed USTAR `production-bundle.tar`, containing `receipt.json` and `output/`.
It does not package the workspace, `.vercel/project.json`, global config, or auth caches.

This first format accepts regular files and directories only. It explicitly rejects **all**
symlinks and hard links, including internal links: none are silently followed, removed, or
flattened. Unsupported topology is a failure requiring review, not an invitation to change
the output until it passes. Top-level output entries are limited to `config.json`,
`builds.json`, `static/`, and `functions/`; `output/config.json` is required. Other entries
(including output caches), authentication/environment filenames, special permission bits,
extended/sparse TAR headers, duplicates, external paths, and non-USTAR names are rejected.
Names are canonical relative POSIX ASCII paths up to 240 characters and must also be
representable in USTAR's name/prefix fields. This is not a generic Build Output API validator.

The inventory records paths, types, modes, sizes, whole-second mtimes, and file SHA-256s,
without printing file contents. UID/GID and owner names are normalized to zero/empty;
ACLs, xattrs and sub-second times are not transferred. Modes and whole-second mtimes are
restored and checked along with every file's bytes. Unsupported metadata is not certified.

Limits before upload are 64 MiB of file content, 4096 output entries including directories,
2 MiB for the JSON receipt, and 80 MiB for the complete TAR. These conservative limits keep
one candidate well below the smallest documented 100 MB Hobby CLI upload ceiling and leave
room for TAR headers/padding; they do **not** prove current free storage availability or
Vercel acceptance. Upload uses the existing CI `upload-artifact` pin, a run/attempt-specific
name, `if-no-files-found:error`, `overwrite:false`, and `retention-days:1`.

### Same-run consumer and integrity

`verify-production-bundle` requires successful `production-build` via `needs` and runs on
a fresh `ubuntu-latest` runner. It has no application checkout, dependency install, cache,
build, Vercel CLI, Environment, or Vercel secret. It never executes received files.

A pre-download check requires a single positive artifact ID, rejecting empty input and lists
before the pinned `download-artifact` action could fall back to broad selection. That ID
comes from the producer's upload output, never latest, a generic name, or a pattern.
The verifier performs only GitHub GETs and requires the exact workflow, repository, branch,
SHA, build run and attempt, current remote master, and a successful producer job of that
attempt. It rejects incomplete/unexpected job listings. **The overall run may still be in
progress**: the verifier belongs to it, so requiring a completed run would deadlock this flow.

The receipt binds repository/SHA, CI run/attempt, build run/attempt, workflow ID, CLI version,
settings SHA-256, and the complete inventory. Its provenance is compared to the consumer's
context and GitHub metadata. Artifact metadata must independently match the ID, run, SHA,
repository IDs, non-expired state and run/attempt-specific name. The verification log joins
that receipt with the artifact ID and both digests; the embedded receipt cannot contain its
own future artifact ID before upload.

Two different hashes are deliberately kept separate:

- `zip_digest`: SHA-256 of GitHub's outer artifact ZIP, from upload output and artifact API.
- `package_sha256`: SHA-256 of the inner TAR, independently passed through a producer job output.

The download action's digest warning is not treated as a gate. The verifier explicitly
aborts if metadata digests differ or the actual TAR does not match `package_sha256`.
The download directory must contain exactly that regular TAR. All TAR names, types, ownership,
receipt fields, hierarchy, modes, sizes, mtimes and content hashes are validated **before**
creating a new extraction directory. No `extractall` is used: only validated regular files
and directories are materialized, followed by a complete content/metadata comparison.

### Required future evidence — not PASS from fixtures

A separately authorized hosted transfer experiment must establish:

1. The actual output tree, file count, byte size, modes and links fit the declared format.
2. The intended artifact contents are appropriate for download from this public repository.
   Filename restrictions and lack of credentials are **not** a secret/content audit.
3. Shared Actions artifact storage has sufficient free quota; one-day retention is a bound,
   not proof of capacity. No paid storage or plan upgrade is authorized.
4. Artifact API outputs, runner permissions and the same-run download work as declared.
5. A second runner reconstructs the intended output without referring to the first workspace.
   Byte/metadata equality alone does not prove operational portability or Vercel acceptance.

Local validation executes the actual inline packaging/verification code on tiny temporary
fixtures and mocked GitHub GETs, including tampering and extraction-boundary negatives.
It does not build, regenerate exports, install dependencies, run the CLI, transfer a real
artifact, or certify Linux/Python 3.13 from auxiliary Windows/Python 3.11 results.

The observed `tar@7.5.7` warning remains an unresolved gate for any future process with a
Vercel token. This unit does not update `vercel@50.39.0`, dependencies or pins. The Environment
was last observed without protection rules; this candidate neither configures it nor calls
it protected. There is no deployment reservation, ledger, `deployments:write`, token,
publisher, promotion, or automatic publication trigger. Each later operation needs its own
authorization; GREEN does not grant publication, enablement, dispatch or deployment.
