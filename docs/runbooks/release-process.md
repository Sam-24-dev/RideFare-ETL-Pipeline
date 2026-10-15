# Release Process

## Purpose

This runbook documents RideFare's PR-only release preparation. It does not authorize
workflow reactivation, tags, GitHub Releases, or deployment.

## Release Mechanism

RideFare uses `release-please` from GitHub Actions:

- workflow: `.github/workflows/release-please.yml`
- config: `release-please-config.json`
- manifest: `.release-please-manifest.json`
- version source of truth: `pyproject.toml`

The action is pinned to commit `5c625bfb5d1ff62eadeeb3772007f7f66fdcf071`
(`release-please-action` v4.4.1, with core 17.3.0 locked). This is the action commit,
not the annotated `v4` tag object. `skip-github-release: true` disables the action's
tag/release creation; `skip-github-pull-request` is omitted and defaults to false.
The fixed concurrency group is `release-please-master`, with `cancel-in-progress: false`.

PR-only does not mean read-only: `contents: write` supports release branch/commit
management, and `pull-requests: write` supports PR management. The action keeps its
default `github.token`; no PAT, GitHub App, or additional secret is introduced.

Versioned configuration and administrative state are separate. Release Please remains
`disabled_manually` at the R0-PR2C checkpoint, so it will not open PRs automatically.
Preparing, publishing, or integrating this policy does not reactivate it. Recovery still
requires integrity, permission, and CI/branch-protection readiness checks, followed by
new individual authorization to enable the workflow.

## Commit Convention

Release automation depends on conventional commits.

Use these prefixes for releasable work:

- `feat:` for new functionality
- `fix:` for bug fixes
- `deps:` for dependency changes
- `docs:` may also count for Python release flows when documentation should surface in
  the changelog

Avoid vague commit subjects. Each commit should tell release automation whether the
change should appear in the next version.

## Expected Flow After Separate Reactivation

1. Validated conventional commits land on `master` through pull requests
2. A push may let `release-please.yml` open or update a release PR; this is not guaranteed
   when releasable commits or other required conditions are missing
3. The release PR proposes updates to:
   - `CHANGELOG.md`
   - `pyproject.toml`
   - `.release-please-manifest.json`
4. Validate the release PR with required CI; its merge needs separate authorization
5. Merging it does not make this workflow create tags or a GitHub Release. Future
   publication requires a separate mechanism and owner authorization

## PR Creation, Run Approval, and Review

These are three different controls:

- **PR creation:** the default token needs the explicit workflow permissions above and
  the repository setting allowing Actions to create/approve PRs. The Actions default
  token permission remains `read`; it does not remove those explicit workflow grants.
- **Workflow execution approval:** current [GitHub documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)
  says PRs created/updated with `GITHUB_TOKEN` on `opened`, `synchronize`, or `reopened`
  create runs requiring approval by a user with write access. Do not assume CI can never
  run, or that it runs without approval. Do not introduce credentials to bypass this gate.
- **PR review/merge:** approving a run is not an approving PR review or permission to
  merge. The minimum `master` protection requires zero approving reviews, but its required
  checks and up-to-date requirement still apply.

No approval or reactivation is performed by this policy test or documentation.

## Bootstrap History and Current State

- `0.1.0` was the historical bootstrap version, not the current manifest value
- at the R0-PR2C checkpoint, the manifest and `pyproject.toml` remain at `0.2.1`
- do not reinitialize the manifest or force a version/release to provoke a PR
- if no release PR appears after separately authorized recovery, inspect releasable
  commits, administrative state, permissions, and any existing `autorelease: pending`
  state; do not repair labels or release state automatically

## Operational Advice

- manifest or release-state repair requires a separate decision and authorization;
  it is not part of this policy change
- treat `pyproject.toml` as the repository version source
- do not version the frontend independently from the repository root during the current
  portfolio build
