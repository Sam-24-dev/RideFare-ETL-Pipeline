# Release Process

## Purpose

This runbook documents how RideFare versions releases after `Deployment and Automation`.

## Release Mechanism

RideFare uses `release-please` from GitHub Actions:

- workflow: `.github/workflows/release-please.yml`
- config: `release-please-config.json`
- manifest: `.release-please-manifest.json`
- version source of truth: `pyproject.toml`

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

## Expected Flow

1. Work lands on `master` through reviewed pull requests
2. `release-please.yml` updates or opens a release PR
3. The release PR updates:
   - `CHANGELOG.md`
   - `pyproject.toml`
4. Merge the release PR when you want to cut a new version
5. GitHub Release is published from the merged release PR

## First Bootstrap Notes

- the manifest is initialized at version `0.1.0`
- the first releasable commit after this setup should open the first release PR
- if no release PR appears, confirm:
  - commits use conventional commit prefixes
  - no stale `autorelease: pending` label exists on an older PR

## Operational Advice

- do not edit `.release-please-manifest.json` manually unless you are intentionally
  bootstrapping or repairing release state
- treat `pyproject.toml` as the repository version source
- do not version the frontend independently from the repository root during the current
  portfolio build
