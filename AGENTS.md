# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Next.js app. Source lives in `app/src/app` (routes) and `app/src/lib` (shared code).
- `packages/textutils/`: Shared Python library (normalize v1.1, tokenize v1.0, hashing, citations).
- `data-workbench/`: Canonical CSV-first working surface plus current operational data artifacts. See `data-workbench/README.md`.
- `pipelines/`: Structured Python pipeline modules (`validate/`, `tei_index/`, `vocab_extract/`, `alignment/`). Run via `python -m pipelines.<name>`.
- `scripts/`: Python tooling for CSV validation/import, TEI indexing, vocab import, alignment import, and a zero-dependency Supabase REST client. Being migrated to `pipelines/`.
- `supabase/`: Supabase config and SQL migrations in `supabase/migrations/` (001–007 MVP, TEI-first, RLS, public read).
- `config/`: TEI doc configs (`config/tei_docs/`), test subset, entry ID bridge, alignment seed data.
- `tests/`: Python tests (40 tests) with fixtures for normalization, tokenization, TEI extraction rules, and cross-language parity.
- `docs/`: Active docs, contracts, prompts, workflow notes, and indexes. See `docs/README.md`.
- `archive/`: Historical docs, legacy QC reports, and superseded output families (kept for traceability).
- `outputs/`: LLM extraction results (critical data: 27,707 terms, 2,894 qualities). See `outputs/README.md`.
- `contracts/`: Formal contracts (C-01 TEI indexing, C-02 normalization, C-03 anchoring, C-04 citation, C-05 export, AL-01 alignment).
- `docs/new_simples/`: TEI-first specs, live workflow board, and session log.

## Build, Test, and Development Commands
- Install deps: `npm ci` (root), `npm --prefix app ci`, and `pip install -e ".[dev]"` (Python packages).
- Run all checks (CI parity): `npm run ci`.
- Run textutils tests: `npm run textutils:test` (or `python -m pytest tests/ -v`).
- Run unified validation: `python -m pipelines.validate [--data] [--tei] [--all]`.
- TEI pipeline: `npm run tei:validate`, `npm run tei:index`, `npm run tei:index:dry-run`.
- Import: `npm run vocab:import`, `npm run align:import`.
- Hosted Supabase: `npm run supabase:link` (once) then `npm run db:setup` (migrate + validate + import).
- Dev server: `npm --prefix app run dev` (serves on `http://localhost:3000`).

## Coding Style & Naming Conventions
- Formatting: follow `.editorconfig` (LF, UTF-8, trim trailing whitespace). Use 2-space indent for TS/JS/JSON and 4-space indent for Python.
- Linting: run `npm run app:lint` (ESLint via `app/eslint.config.mjs`) before opening a PR.
- Domain IDs (legacy): entries use `SOURCE-ref` (e.g. `GAL_SMT-6.1.1`); lemmata `L###`, parts `P###`, preparations `PR###`.
- Domain IDs (TEI-first): entries use `tei_doc_id~tei_segment_id` (e.g. `gal_smt~seg_6_1_1`). Delimiter is `~` not `#`.
- Greek normalization v1.1: keep Python (`packages/textutils/normalize.py`), TypeScript (`app/src/lib/greek/normalize.ts`), and SQL (`supabase/migrations/005_tei_first_schema.sql`) implementations in sync. Strips ALL combining marks U+0300–U+036F including iota subscript.

## Testing Guidelines
- Python tests: `python -m pytest tests/ -v` (40 tests covering normalization, tokenization, determinism, cross-language parity).
- CI: `npm run ci` (data validation + lint + build).
- TEI indexer dry-run: `npm run tei:index:dry-run` for non-destructive validation.

## Commit & Pull Request Guidelines
- Commits: use short, imperative subjects; optional scoped prefixes are common (e.g. `data: ...`, `chore: ...`, `Fix ...`).
- PRs: describe intent + approach, list commands run (at least `npm run ci`), call out `supabase/migrations/` changes, and include screenshots for UI changes.

## Working Practices (Keep the Repo Clean)
- Start: review `PRODUCT_PLAN.md`, then `docs/new_simples/new_wbs.md`, then the latest entry in `docs/new_simples/session_log.md`.
- Record structural changes in `CHANGELOG.md` with explicit before→after paths and reasons.
- Refer to `docs/new_simples/tech_spec_v1.md` for architecture decisions.
- Refer to `contracts/` for formal specifications (indexing, normalization, anchoring, citation, export, alignment).
- End: update `docs/new_simples/new_wbs.md`, append a matching handoff note to `docs/new_simples/session_log.md` (including `Transformations:`), update `CHANGELOG.md` if structural changes were made, then commit and leave the working tree clean (`git status`).

## Autonomous Work Roles

Three roles govern how work is planned, executed, and verified. Each role has distinct responsibilities and handoff points. When working autonomously, cycle through all three roles for every unit of work.

### Role 1: Planner
- **Reads**: `PRODUCT_PLAN.md`, `docs/new_simples/new_wbs.md`, `docs/new_simples/session_log.md`, relevant contracts and specs
- **Produces**: A scoped task description with: files to touch, expected changes, acceptance criteria, and verification commands
- **Rules**:
  - Never modifies code or data — read-only exploration
  - Identifies dependencies and ordering constraints
  - Breaks large phases into atomic units (one commit per unit)
  - Flags risks or ambiguities for the user before proceeding

### Role 2: Implementer
- **Reads**: The Planner's task description
- **Produces**: File changes (edits, moves, creates) that satisfy the task
- **Rules**:
  - Follows the plan exactly — no scope creep, no "while I'm here" improvements
  - One logical change at a time
  - Preserves existing patterns and conventions (indentation, naming, structure)
  - If the plan is wrong or incomplete, stops and hands back to Planner — does not improvise

### Role 3: QC / Verifier
- **Reads**: The Implementer's changes + the Planner's acceptance criteria
- **Produces**: A pass/fail verdict with evidence
- **Rules**:
  - Runs all verification commands (`npm run ci`, `python -m pytest tests/ -v`, targeted greps)
  - Checks that no stale references remain (grep for moved/renamed paths)
  - Checks that READMEs and doc maps are consistent with actual file locations
  - If verification fails, hands back to Implementer with specific failure details — does not fix issues itself
  - On pass: updates `docs/new_simples/new_wbs.md` and `docs/new_simples/session_log.md`

### Handoff cycle
```
Planner → task spec → Implementer → changes → QC/Verifier → pass/fail
                                                    ↓ (fail)
                                              Implementer (retry)
                                                    ↓ (pass)
                                              Next task (back to Planner)
```

## Security & Configuration Tips
- Don't commit secrets: use `.env.example` → `.env.local` and `app/.env.example` → `app/.env.local`. The service role key is required for import tooling; store it in local env/CI secrets only.
