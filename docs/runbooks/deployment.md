# Deployment

## Purpose

This runbook explains how RideFare moves from a pull request to preview and then to
production on Vercel.

## Deployment Model

- the public app lives in `apps/web`
- the public app reads static JSON artifacts from `data/processed/analytics/web` and
  `data/processed/ml/web`
- those public artifacts are versioned in git for transparency and local reproducibility
- GitHub Actions is the deploy orchestrator
- Vercel native Git auto-deploy should stay disabled so deploy behavior remains explicit

## GitHub Actions Workflows

- `ci.yml`
  runs Python validation, regenerates public artifacts in workspace, and validates the
  frontend build against those artifacts
- `pipeline-refresh.yml`
  regenerates public artifacts on `master` when backend or data inputs change and commits
  refreshed JSON outputs back to the branch
- `vercel-preview.yml`
  builds a preview deployment for pull requests targeting `master`
- `vercel-production.yml`
  builds and deploys production on `master`

## Required GitHub Secrets

Add the following repository secrets before enabling the Vercel workflows:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

The repository also needs GitHub Actions `contents: write` permission so
`pipeline-refresh.yml` can commit refreshed artifacts.

## Required Vercel Project Settings

- framework preset: `Next.js`
- Node version: `22`
- root directory: `apps/web`
- native Git auto-deploy: disabled

The app must receive `RIDEFARE_PROJECT_ROOT` at build time. The workflows set it to
`${{ github.workspace }}` so the loaders can resolve `data/processed/**` from the
repository root during `vercel build`.

## Manual Preview Checklist

1. Open or update a pull request targeting `master`
2. Confirm `ci.yml` passes
3. Confirm `vercel-preview.yml` publishes a preview URL
4. Validate `/`, `/dashboard`, `/como-funciona`, and `/escenarios` in the preview
5. Merge only after the preview matches the repository state

## Manual Production Checklist

1. Merge a validated pull request into `master`
2. Confirm `vercel-production.yml` finishes successfully
3. Open the production deployment and verify:
   - Home
   - Dashboard
   - `/como-funciona`
   - `Escenarios`
4. Confirm the app reads the expected artifacts without missing-state banners
