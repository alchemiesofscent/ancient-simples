# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ancient Simples is a scholarly web application for editors working with ancient Greek medical texts — specifically Galen (*De simplicium medicamentorum* VI–XI, *De alimentorum facultatibus*), Oribasius (*Collectiones Medicae* 15), and Aetius (*Libri Medicinales* I–II). It comprises ~1,699 entries across four source texts.

The project has two main parts: a **CSV-first data pipeline** that transforms a source spreadsheet into normalized CSVs and imports them into Supabase, and a **Next.js web app** for browsing and editing entries. There is no separate backend service — the MVP constraint is Next.js + Supabase only.

## Commands

### CI (runs all checks)
```
npm run ci
```
This runs: data validation → app lint → app build.

### Individual checks
```
npm run data:validate          # Python: validate data-workbench CSVs
npm run app:lint               # ESLint on the Next.js app
npm run app:build              # Next.js production build
```

### Database
```
npm run supabase:link          # Link to hosted Supabase project
npm run db:push                # Push migrations to Supabase
npm run db:import              # Python: import CSVs into Supabase (needs SUPABASE_SERVICE_ROLE_KEY)
npm run db:setup               # db:push + data:validate + db:import
```

### App development
```
npm --prefix app run dev       # Start Next.js dev server (localhost:3000)
```

### Install dependencies
```
npm ci                         # Root (Supabase CLI)
npm --prefix app ci            # App (Next.js + deps)
```

## Architecture

### Workspace layout
- `app/` — Next.js 16 app (App Router, TypeScript, Tailwind v4, `@supabase/ssr`)
- `data-workbench/` — Source spreadsheet (`simples.xlsx`), Python `make_*.py` scripts that produce CSVs, and QC reports
- `scripts/` — Python scripts for validation (`validate_data.py`), import (`import_supabase.py`), vocab extraction runners, and a zero-dependency Supabase REST client (`supabase_rest.py`)
- `supabase/migrations/` — SQL migrations (schema, RLS policies, Greek normalization function)
- `schemas/` — JSON schemas (e.g. for LLM-based vocab term extraction)
- `docs/` — Project specs and domain reference:
  - `simples_prd.md` — Product requirements (authoritative scope for MVP vs Phase 2)
  - `simples_technical_review.md` — Architecture decisions and rationale
  - `simples_implementation_guide.md` — Step-by-step implementation walkthrough
  - `simples_data_restructure_spec.md` — How the legacy spreadsheet becomes normalized CSVs
  - `lemma_rules.md` — Controlled vocabulary rules: label taxonomy (SUBSTANCE, PART, PREPARATION, PROCESS, TOOL_CONTAINER, CONDITION, QUALITY_PROPERTY, APPLICATION_SITE), normalization requirements, borderline adjudication rules, and MWE handling
  - `prompts/` — LLM prompt templates for vocab term extraction
  - `new_simples/` — Specs for planned new features/texts

### Data flow
1. `data-workbench/make_*.py` scripts transform `simples.xlsx` → CSVs (entries, lemmata, parts, preparations, entry_preparations)
2. `scripts/validate_data.py` validates CSV integrity (FK refs, normalization, uniqueness)
3. `scripts/import_supabase.py` upserts CSVs into Supabase via REST API (uses service role key, bypasses RLS)

The `lemma_ids` column in `entries.csv` is **import-only** — it gets exploded into `entry_lemmata` junction rows during import and is never read by the app.

### Database schema (Supabase/Postgres)
Core tables: `entries`, `lemmata`, `parts`, `preparations`, `editions`. Junction tables: `entry_lemmata`, `entry_preparations`, `entry_references`, `annotations`. Auth: `profiles` (viewer/editor roles via RLS).

Key behaviors:
- `normalize_greek()` PL/pgSQL function strips diacritics (except iota subscript) for prefix search
- `entries.greek_normalized` is auto-populated by trigger on insert/update
- Prefix search uses `LIKE 'prefix%'` with `text_pattern_ops` index; minimum 3 normalized characters
- `lemmata` has self-referential FK (`parent_lemma`) — import uses two-pass upsert (nulls first, then real values)
- RLS pattern: all tables are `authenticated read + editor write`; `profiles` gates viewer/editor roles

### Next.js app (`app/src/`)
- Uses **server components** exclusively (no client components yet)
- `src/lib/supabase/server.ts` — Server-side Supabase client (cookie-based auth)
- `src/lib/supabase/browser.ts` — Browser-side Supabase client
- `src/lib/greek/normalize.ts` — TypeScript Greek normalization (must match the Python and SQL versions)
- `middleware.ts` — Auth guard redirecting unauthenticated users to `/login`; public routes: `/`, `/login`, `/auth/callback`
- Routes: `/` redirects to `/entries`, `/entries` (search/list), `/entries/[entry_id]` (detail + editor form)
- Editors can update `translation` and `trans_status` via server action; viewers are read-only
- Auth: Supabase email magic links; new signups default to `viewer` role

### Greek normalization
Three implementations that **must stay in sync**: Python (`scripts/validate_data.py:normalize_greek_for_match`), TypeScript (`app/src/lib/greek/normalize.ts`), SQL (`supabase/migrations/001_init.sql:normalize_greek`). All lowercase, strip combining marks U+0300–U+036F except iota subscript U+0345, NFC output. No transliteration, no morphology, no lemmatization.

### Vocab extraction tooling
`scripts/vocab_agent_runner.py` and `scripts/vocab_multi_agent_pilot.py` run LLM-based term extraction over entry texts using the label taxonomy defined in `docs/lemma_rules.md`. Output schemas live in `schemas/`. Prompt templates live in `docs/prompts/`.

## Domain Conventions
- Sources are identified by codes: `GAL_SMT`, `GAL_ALIM`, `ORIB_CM`, `AET_LM`
- Entry IDs follow `SOURCE-ref` pattern (e.g. `GAL_SMT-6.1.1`)
- Lemma IDs are sequential (`L001`, `L002`, …); part IDs are `P###`; preparation IDs are `PR###`
- Categories for lemmata: `vegetable`, `animal`, `mineral`
- Translation status lifecycle: `draft` → `review` → `final`
- CSVs use literal `\n` tokens for newlines within fields (not physical newlines)

## MVP vs Phase 2 Boundary
Currently implemented (MVP/Phase 1): entry browser, prefix Greek search, translation editing, role-based auth. Explicitly deferred to Phase 2+: annotation system with re-anchoring, columnar comparative view, redactor view, TEI export, rich text editing, real-time collaboration, public API.

## Environment
- Node.js 20+, Python 3.12+
- Root `.env.local` — `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (for import scripts)
- `app/.env.local` — `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (for Next.js)
- Python scripts use stdlib only (no pip dependencies) plus local `supabase_rest.py`
