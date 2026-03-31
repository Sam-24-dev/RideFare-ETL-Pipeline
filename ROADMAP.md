# RideFare Roadmap

## Purpose

This roadmap turns the current repository from a notebook-centered ETL demo into a polished data product that showcases:

- Data Engineering
- Analytics Engineering
- Data Science / Machine Learning
- Product-grade frontend delivery

The public UI will be in Spanish. The repository documentation, code comments, commits, and technical artifacts will be in English.

## Target End State

The finished project should provide:

- A reproducible data pipeline built with `Polars`, `DuckDB`, `dbt`, and `Pandera`
- A documented ML workflow built with `scikit-learn`, `XGBoost`, and `SHAP`
- A premium public web app built with `Next.js`, `TypeScript`, `Tailwind CSS`, `shadcn/ui`, `Framer Motion`, and `Apache ECharts`
- Automated validation and deployment through `GitHub Actions`
- Public documentation that reads like a strong portfolio project, not an academic exercise

## Non-Negotiable Rules

- The notebook is not the source of truth
- Production logic must live in Python, SQL, and TypeScript code
- No new core technologies are added without documenting the reason
- No generic dashboard UI
- No hidden manual steps
- Every phase must end with working validation

## Target Repository Structure

```text
RideFare/
  apps/
    web/
  src/
    ridefare/
  dbt/
  data/
    raw/
    external/
    interim/
    processed/
    samples/
  notebooks/
  docs/
    architecture/
    adr/
    data/
    ml/
    ui/
    runbooks/
  scripts/
  tests/
  .github/
    workflows/
  AGENTS.md
  ROADMAP.md
  README.md
  pyproject.toml
  pnpm-workspace.yaml
  .env.example
```

## Phase Plan

### Phase 1: Foundation

**Goal**

Create the project skeleton, developer tooling, standards, and initial documentation so future work happens inside a controlled structure.

**Mini-Phases**

1. Audit the legacy repository and preserve only reusable logic and assets
2. Create the new repository layout
3. Set up Python, Node, and shared project tooling
4. Set up linting, formatting, and test runners
5. Write initial architecture and operating docs

**Deliverables**

- New folder layout in place
- `pyproject.toml`, workspace config, environment example files
- Base Python package in `src/ridefare`
- Base Next.js app in `apps/web`
- Initial `README.md`, `docs/architecture/system-overview.md`, and first ADRs
- `AGENTS.md` and this roadmap committed as the operating guides

**Validation Gates**

- Python environment installs cleanly
- Frontend dependencies install cleanly
- Basic lint and test commands run without repo edits
- Project structure is coherent and discoverable

### Phase 2: Data Platform

**Goal**

Build a reproducible analytics pipeline that ingests, validates, transforms, and models the ride and weather data.

**Mini-Phases**

1. Build ingestion modules for raw rides and weather files
2. Normalize schema, timestamps, and field names
3. Add `Pandera` contracts for each dataset layer
4. Store clean outputs in `Parquet`
5. Create `DuckDB` analytical layer
6. Build `dbt` models for `staging`, `intermediate`, and `marts`
7. Add dbt tests and data-quality checks

**Deliverables**

- Ingestion package
- Data contracts
- Clean Parquet outputs
- DuckDB database or reproducible query layer
- `dbt` project with marts ready for analytics and ML
- Quality checks with pass/fail behavior

**Validation Gates**

- Ingestion runs end-to-end from raw inputs
- Schema validation catches bad inputs
- dbt models build successfully
- Data marts expose stable outputs for the frontend and ML layer

### Phase 3: ML System

**Goal**

Turn the current notebook modeling into a repeatable ML workflow with baseline comparison, explainability, and exportable artifacts.

**Mini-Phases**

1. Define modeling dataset and feature contract
2. Implement baseline models
3. Implement primary model with `XGBoost`
4. Add evaluation pipeline with temporal split
5. Generate SHAP explanations and comparison visuals
6. Export model artifacts for the web product
7. Document the model with a model card and evaluation protocol

**Deliverables**

- Feature builder
- Baseline and primary models
- Evaluation reports
- Feature importance and SHAP outputs
- Static JSON or Parquet exports for frontend consumption
- `docs/ml/model-card.md`

**Validation Gates**

- Training runs reproducibly from modeled data
- Metrics are versioned and comparable across runs
- Outputs are stable enough for frontend rendering
- Model limitations are documented explicitly

### Phase 4: Web Product

**Goal**

Build a public-facing app in Spanish that looks like a real data product and explains the project clearly.

**Mini-Phases**

1. Define the visual system and product tone
2. Build the shell, navigation, and layout system
3. Build the marketing/home page
4. Build the analytics dashboard
5. Build the methodology page
6. Build the model lab page
7. Build the scenario simulator from exported artifacts
8. Polish responsive behavior, accessibility, and motion

**Deliverables**

- Home page
- Dashboard page
- Methodology page
- Model lab page
- Shared data layer and chart components
- Mobile-ready and desktop-ready UI

**Validation Gates**

- Frontend builds successfully on local and CI
- All public pages render with typed data contracts
- Layout remains usable on mobile and desktop
- Lighthouse and accessibility checks are acceptable for a portfolio project

### Phase 5: Deployment and Automation

**Goal**

Automate validation, data refresh, and web deployment with minimal manual intervention.

**Mini-Phases**

1. Create CI for Python and frontend
2. Create pipeline refresh workflow
3. Export static artifacts for the web app
4. Connect the frontend to Vercel
5. Add release automation with `release-please`

**Deliverables**

- CI workflow
- Pipeline refresh workflow
- Vercel-ready frontend
- Release workflow and changelog automation

**Validation Gates**

- CI passes on main paths
- Pipeline workflow can rebuild exports
- Vercel preview and production deploys succeed
- Releases can be generated from conventional commits

### Phase 6: Portfolio Polish

**Goal**

Package the repository as a standout portfolio project for data roles.

**Mini-Phases**

1. Rewrite the README as a portfolio asset
2. Curate screenshots and narrative visuals
3. Tighten docs, ADRs, and runbooks
4. Review consistency across repo, UI, and messaging

**Deliverables**

- Strong portfolio README
- Updated screenshots
- Final architecture docs
- Final model documentation
- Operational runbooks

**Validation Gates**

- A reviewer can understand the project without opening the notebook
- Docs, UI, and code tell the same story
- The project looks intentional and complete

## Cross-Phase Validation Standards

Every phase must include the following before moving forward:

- Code compiles or runs for the touched area
- Relevant tests exist and pass
- Documentation is updated if behavior changed
- Visual changes are checked in a browser if frontend is affected
- The change stays inside the current phase scope

## Public Interfaces Expected Over Time

The implementation should converge to these interfaces:

- Python commands or scripts for `ingest`, `transform`, `train`, and `export-web`
- Stable dbt marts for analytics and ML
- Static data artifacts for frontend pages and simulator inputs
- Typed frontend data contracts for all loaded datasets

## Deferred Items

The following are intentionally out of scope for the first full build:

- Auth
- User accounts
- Live online inference API
- Supabase-backed application state
- Figma-based workflow without a token and real design assets
- Additional orchestration platforms unless the current stack becomes insufficient

## Completion Criteria

The roadmap is complete when:

- The old notebook is no longer the operational center of the repo
- The pipeline is reproducible and validated
- The ML workflow is documented and explainable
- The public web app is polished and deployed
- The repo reads like a professional portfolio project
