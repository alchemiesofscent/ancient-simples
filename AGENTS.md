# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Next.js app. Source lives in `app/src/app` (routes) and `app/src/lib` (shared code).
- `packages/textutils/`: Shared Python library (normalize v1.1, tokenize v1.0, hashing, citations).
- `data-workbench/`: Spreadsheet + `make_*.py` transforms that produce the CSV outputs.
- `scripts/`: Python tooling for CSV validation/import, TEI indexing, vocab import, alignment import, and a zero-dependency Supabase REST client.
- `supabase/`: Supabase config and SQL migrations in `supabase/migrations/` (001–004 MVP, 005–006 TEI-first).
- `config/`: TEI doc configs (`config/tei_docs/`), test subset, entry ID bridge, alignment seed data.
- `tests/`: Python tests (35 tests) with fixtures for normalization, tokenization, and TEI extraction rules.
- `docs/`: Specs, contracts, prompts, WBS. `schemas/`: JSON schemas. `outputs/`: vocab extraction results.
- `docs/contracts/`: Formal contracts (C-01 TEI indexing, C-02 normalization, C-03 anchoring, C-04 citation, C-05 export, AL-01 alignment).
- `docs/new_simples/`: TEI-first specs (tech_spec_v1, ux_spec_v1, wbs_v1).

## Build, Test, and Development Commands
- Install deps: `npm ci` (root) and `npm --prefix app ci`.
- Run all checks (CI parity): `npm run ci`.
- Run textutils tests: `npm run textutils:test` (or `python -m pytest tests/ -v`).
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
- Python tests: `python -m pytest tests/ -v` (35 tests covering normalization, tokenization, determinism).
- CI: `npm run ci` (data validation + lint + build).
- TEI indexer dry-run: `npm run tei:index:dry-run` for non-destructive validation.

## Commit & Pull Request Guidelines
- Commits: use short, imperative subjects; optional scoped prefixes are common (e.g. `data: ...`, `chore: ...`, `Fix ...`).
- PRs: describe intent + approach, list commands run (at least `npm run ci`), call out `supabase/migrations/` changes, and include screenshots for UI changes.

## Working Practices (Keep the Repo Clean)
- Start: review `docs/new_simples/wbs_v1.md` for current status and next tasks.
- Refer to `docs/new_simples/tech_spec_v1.md` for architecture decisions.
- Refer to `docs/contracts/` for formal specifications (indexing, normalization, anchoring, citation, export, alignment).
- End: commit and leave the working tree clean (`git status`).

## Security & Configuration Tips
- Don't commit secrets: use `.env.example` → `.env.local` and `app/.env.example` → `app/.env.local`. The service role key is required for import tooling; store it in local env/CI secrets only.
