# AGENTS.md

## Mission

Build RideFare as a premium hybrid portfolio project that demonstrates strong Data Engineering, Analytics Engineering, and Machine Learning execution, with a polished Spanish-language public interface and English technical documentation.

This file must be read before every iteration.

## Project Rules

- Public UI copy is in Spanish
- Repository docs, technical docs, code comments, commits, and PR titles are in English
- The notebook is not the source of truth
- Production logic belongs in Python, SQL/dbt, and TypeScript
- No emojis in docs, code comments, logs, commits, or UI
- No decorative comments
- Add comments only when they explain non-obvious rationale
- Do not introduce new core technologies without documenting why
- Do not jump to later phases if an earlier phase is incomplete

## Approved Stack

### Frontend

- `Next.js`
- `TypeScript`
- `Tailwind CSS`
- `shadcn/ui` as a base, heavily customized
- `Framer Motion`
- `Apache ECharts`
- Deploy target: `Vercel`

### Data

- `Polars`
- `DuckDB`
- `dbt`
- `Pandera`
- `Parquet`

### ML

- `scikit-learn`
- `XGBoost`
- `SHAP`

### Quality and Automation

- `pytest`
- `Ruff`
- `GitHub Actions`
- `release-please`

## Canonical Repository Areas

- `apps/web`: public product
- `src/ridefare`: production Python package
- `dbt`: transformation and analytics modeling
- `data`: local data zones
- `notebooks`: exploration and diagnostics only
- `docs`: architecture, ADRs, runbooks, data docs, ML docs, UI docs
- `tests`: unit, integration, data-quality, contract tests

## Phase Execution Policy

Always work in the current active phase and its next unfinished mini-phase.

### Phase Order

1. Foundation
2. Data Platform
3. ML System
4. Web Product
5. Deployment and Automation
6. Portfolio Polish

### Mini-Phase Rule

For each large phase:

1. Finish one mini-phase completely
2. Validate it
3. Update docs if behavior changed
4. Then move to the next mini-phase

Do not mix unfinished work from multiple large phases unless blocked by a strict dependency.

## Definition of Done Per Iteration

An iteration is complete only if all apply:

- The change fits the current phase and mini-phase
- The touched code paths run or build successfully
- Relevant tests were added or updated
- Relevant validation commands were run
- Docs were updated if the change altered behavior or structure
- No production logic was hidden inside notebooks

## Skills to Use

Use the smallest set of skills that fits the task. Do not load extra skills without reason.

### Planning and Structure

- `architecture`
  Use for repo structure, ADRs, phase design, and system decisions

- `brainstorming`
  Use when a decision is still open and needs comparison before implementation

- `doc-coauthoring`
  Use when writing or restructuring README, ADRs, architecture docs, model docs, or runbooks

### Backend and Data

- `test-driven-development`
  Use before significant feature or bugfix implementation

- `python-patterns`
  Use for Python package design, modular ETL code, and clean implementation style

- `python-testing`
  Use for test design in Python modules and pipelines

- `pytest`
  Use when creating or refining pytest-based tests

- `database-migrations`
  Use only if the project evolves into managed relational schema migration work

### Frontend and UX

- `frontend-design`
  Use before building or restyling public UI sections

- `ui-ux-pro-max`
  Use for product-level polish, hierarchy, layout, and interaction quality

- `web-design-guidelines`
  Use for final frontend review and accessibility/UX checks

### Validation

- `lint-and-validate`
  Use after every coding phase

- `verification-loop`
  Use before declaring major milestones done

- `playwright`
  Use when browser automation or flow validation is needed

- `vercel-deploy`
  Use when deployment behavior or Vercel workflows need to be validated

## MCP Usage Policy

Use MCPs only when they improve accuracy or save implementation risk.

### MCPs currently useful for this project

- `context7`
  Use for up-to-date library and framework documentation
  Typical moments: Next.js, dbt, DuckDB, Tailwind, Pandera, XGBoost, Vercel configuration

- `github`
  Use for repository metadata, PR context, workflow review, or release automation research

- `chrome-devtools`
  Use for frontend inspection, layout debugging, accessibility checks, screenshots, and Lighthouse

- `playwright`
  Use for end-to-end validation of the web product

- `TestSprite`
  Use optionally after the app is running and stable enough for generated test plans

- `web`
  Use for official docs and any fact that may have changed over time

### MCPs not to use as the main path

- `powerbi`
  Optional side deliverable only

- `toolbox-db`
  Not a core project tool for the current architecture

## When to Add New Skills or MCPs

Do not import new skills or MCPs by default.

Add them only when all are true:

- The current task is blocked or materially weakened without them
- Existing installed skills or MCPs cannot solve the need well
- The new tool directly supports the active phase
- Any required credentials already exist
- The tool does not drag the project away from the approved stack

### Good moments to add a new skill or MCP

- At the start of a new large phase
- Before a highly specialized implementation
- Before a validation stage that current tools cannot cover

### Bad moments to add a new skill or MCP

- Mid-iteration without a clear blocker
- Just because a tool looks interesting
- When it duplicates an existing capability
- When it requires credentials that do not exist yet

If a new skill or MCP becomes a persistent part of the workflow, document the reason in the relevant doc or ADR.

## Validation Matrix

### Foundation

- Run Python environment checks
- Run frontend install/build smoke checks
- Validate base lint and test commands

### Data Platform

- Validate schema contracts
- Run ingestion and transform flow
- Run dbt build and tests
- Validate output dataset shapes

### ML System

- Run training and evaluation flow
- Validate metric outputs and artifact generation
- Confirm model artifacts match frontend consumption needs

### Web Product

- Run frontend typecheck
- Run frontend build
- Validate pages in browser
- Check responsive behavior
- Run accessibility and performance checks where relevant

### Deployment and Automation

- Validate CI workflows
- Validate artifact export flow
- Validate Vercel build compatibility

### Portfolio Polish

- Re-read docs for consistency
- Check screenshots and naming consistency
- Confirm the repo tells one coherent story

## Iteration Checklist

Before changing code:

1. Read `AGENTS.md`
2. Identify the current phase
3. Identify the next unfinished mini-phase
4. Select the minimum required skills and MCPs
5. Confirm the task stays inside current scope

During implementation:

1. Keep logic inside the correct layer
2. Avoid notebook-driven shortcuts
3. Keep modules small and typed
4. Avoid unnecessary comments and decorative code

After implementation:

1. Run relevant validation
2. Inspect browser behavior if UI changed
3. Update docs if behavior or structure changed
4. Record any important decision in docs or ADRs when needed

## Language Policy

- UI text: Spanish
- README and technical docs: English
- Code comments: English
- ADRs and runbooks: English
- Internal chat with the user: Spanish

## What This Project Must Not Become

- A notebook with a prettier wrapper
- A random collection of technologies
- A backend-heavy app with no portfolio clarity
- A generic SaaS dashboard
- A toolchain demo with weak business storytelling

## Success Standard

The repository should look like a deliberate product:

- technically rigorous
- visually distinctive
- reproducible
- documented
- credible for Data Engineer, Data Analyst, and Data Scientist roles
