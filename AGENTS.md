# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Next.js app. Source lives in `app/src/app` (routes) and `app/src/lib` (shared code).
- `data-workbench/`: Spreadsheet + `make_*.py` transforms that produce the CSV outputs.
- `scripts/`: Python tooling for CSV validation/import and vocab extraction experiments.
- `supabase/`: Supabase config and SQL migrations in `supabase/migrations/`.
- `docs/`: Specs/prompts/WBS. `schemas/`: JSON schemas. `outputs/`: local artifacts (gitignored).

## Build, Test, and Development Commands
- Install deps: `npm ci` (root) and `npm --prefix app ci`.
- Run all checks (CI parity): `npm run ci`.
- Hosted Supabase: `npm run supabase:link` (once) then `npm run db:setup` (migrate + validate + import).
- Dev server: `npm --prefix app run dev` (serves on `http://localhost:3000`).

## Coding Style & Naming Conventions
- Formatting: follow `.editorconfig` (LF, UTF-8, trim trailing whitespace). Use 2-space indent for TS/JS/JSON and 4-space indent for Python.
- Linting: run `npm run app:lint` (ESLint via `app/eslint.config.mjs`) before opening a PR.
- Domain IDs: entries use `SOURCE-ref` (e.g. `GAL_SMT-6.1.1`); lemmata `L###`, parts `P###`, preparations `PR###`.
- Greek normalization: keep Python (`scripts/`), TypeScript (`app/src/lib/greek/`), and SQL (`supabase/migrations/`) implementations in sync when changing rules.

## Testing Guidelines
There’s no dedicated unit test runner yet. Treat `npm run ci` as required and note any manual verification in PRs (UI, data, migrations).

## Commit & Pull Request Guidelines
- Commits: use short, imperative subjects; optional scoped prefixes are common (e.g. `data: ...`, `chore: ...`, `Fix ...`).
- PRs: describe intent + approach, list commands run (at least `npm run ci`), call out `supabase/migrations/` changes, and include screenshots for UI changes.

## Working Practices (Keep the Repo Clean)
- Start: review `docs/new_simples/new_wbs.md`, then run `git status` to confirm the working tree is clean.
- Keep `docs/new_simples/new_wbs.md` as the single WBS/checklist (avoid parallel “plan” docs).
- End: update the WBS checklist (done/next/notes), then commit and leave the working tree clean (`git status`).

## Security & Configuration Tips
- Don’t commit secrets: use `.env.example` → `.env.local` and `app/.env.example` → `app/.env.local`. The service role key is required for import tooling; store it in local env/CI secrets only.
