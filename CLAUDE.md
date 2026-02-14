# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ancient Simples is a scholarly web application for editors working with ancient Greek medical texts — specifically Galen (*De simplicium medicamentorum* VI–XI, *De alimentorum facultatibus*), Aetius (*Libri Medicinales* I–II), Dioscorides (*De Materia Medica*), and others. It comprises ~1,699+ entries across multiple source texts.

The project is transitioning from a **CSV-first** pipeline to a **TEI-first** architecture where TEI XML editions (from the CMG Digital Corpus) are the canonical source for Greek text and citation structure. SQL stores rebuildable caches (entries, tokens, citations) plus editorial layers (translations, lemma links, assertions). See `docs/new_simples/tech_spec_v1.md` for the full architecture.

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
npm run textutils:test         # Python: textutils library tests (35 tests)
```

### TEI pipeline
```
npm run tei:validate           # Validate TEI XML against doc config
npm run tei:index              # Index TEI → Supabase (tei_entries, tokens, refs)
npm run tei:index:dry-run      # Dry-run: JSON report without DB writes
npm run vocab:import           # Import vocab v3 results → assertions + lemmata
npm run align:import           # Import cross-author alignment data
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
- `packages/textutils/` — Shared Python library: normalize (v1.1), tokenize (v1.0), hashing, citations
- `data-workbench/` — Source spreadsheet (`simples.xlsx`), Python `make_*.py` scripts that produce CSVs, and QC reports
- `scripts/` — Python scripts:
  - `validate_data.py` — CSV validation
  - `import_supabase.py` — CSV → Supabase import
  - `validate_tei.py` — TEI XML validation against doc config
  - `index_tei.py` — TEI indexer (extract entries, tokens, citations → Supabase)
  - `import_vocab_v3.py` — Vocab v3 extraction results → assertions + lemma candidates
  - `import_alignments.py` — Cross-author alignment data → Supabase
  - `supabase_rest.py` — Zero-dependency Supabase REST client
- `supabase/migrations/` — SQL migrations (001–006: MVP schema, TEI-first schema, RLS)
- `config/` — TEI doc configs, test subset, entry ID bridge, alignment seed data
- `tests/` — Python tests (35 tests) with fixtures for normalization, tokenization, TEI rules
- `docs/` — Project specs and domain reference:
  - `new_simples/tech_spec_v1.md` — TEI-first architecture and schema
  - `new_simples/ux_spec_v1.md` — Routes, screens, workflows
  - `new_simples/wbs_v1.md` — Work breakdown structure with milestones
  - `contracts/` — Formal contracts: TEI indexing (C-01), normalization (C-02), anchoring (C-03), citation (C-04), export (C-05), alignment interchange (AL-01)
  - `lemma_rules.md` — Controlled vocabulary taxonomy
  - `prompts/` — LLM prompt templates for vocab extraction
- `outputs/` — Vocab extraction results (v1–v3), experiments, pilot runs
- `schemas/` — JSON schemas for LLM-based vocab term extraction

### Data flow (TEI-first)
1. TEI XML files (from CMG submodule at `tei/cmg/`) are the canonical source
2. `scripts/validate_tei.py` checks TEI structure against doc config YAML
3. `scripts/index_tei.py` extracts reading stream, tokens, citations → upserts to `tei_entries`, `tei_tokens`, `tei_entry_refs`
4. `scripts/import_vocab_v3.py` reads extraction results + bridge CSV → creates assertions + lemma candidates
5. `scripts/import_alignments.py` reads alignment JSONL → creates cross-author links

### Data flow (legacy CSV pipeline)
1. `data-workbench/make_*.py` scripts transform `simples.xlsx` → CSVs
2. `scripts/validate_data.py` validates CSV integrity
3. `scripts/import_supabase.py` upserts CSVs into Supabase

### Database schema (Supabase/Postgres)

**Legacy MVP tables** (migrations 001–004): `entries`, `lemmata`, `parts`, `preparations`, `editions`, junction tables, `profiles`.

**TEI-first tables** (migrations 005–006): `tei_sources`, `tei_docs`, `tei_entries` (integer surrogate PK), `tei_tokens`, `tei_entry_refs`, `import_runs`, `tei_translations`, `tei_assertions` (JSONB payload + CHECK constraints), `tei_lemmata`, `tei_lemma_forms`, `tei_entry_lemma_forms`, `tei_lemma_aliases`, `tei_entry_alignments`, controlled vocab tables (`quality_vocab`, `parts_vocab`, `process_vocab`).

Key design decisions:
- Entry ID delimiter: `~` (not `#` — fragment marker breaks URLs). Display ID = `{tei_doc_id}~{tei_segment_id}`
- Integer surrogate PK on `tei_entries` — tokens FK to integer, not text
- Dual hashing: `raw_hash` (pre-normalization) for staleness, `normalized_hash` (post-normalization) for idempotency
- Soft delete via `is_active` + `last_import_run_id`
- JSONB assertions with CHECK constraints per type + expression indexes for facet queries
- Conservative lemma model: `tei_lemma_forms` (strings) linked immediately; `tei_lemmata` (concepts) only via curator confirmation
- RLS: 3 tiers — read-only reference, indexer-owned (service-role), editor-owned (authenticated)

### Next.js app (`app/src/`)
- Uses **server components** exclusively (no client components yet)
- `src/lib/supabase/server.ts` — Server-side Supabase client (cookie-based auth)
- `src/lib/supabase/browser.ts` — Browser-side Supabase client
- `src/lib/greek/normalize.ts` — TypeScript Greek normalization v1.1
- `src/lib/citations/format.ts` — Citation formatting (structure refs, edition refs, combined)
- `middleware.ts` — Auth guard; public routes: `/`, `/login`, `/auth/callback`
- Routes: `/entries` (search/list), `/entries/[entry_id]` (detail + editor form)

### Greek normalization (v1.1)
Three implementations that **must stay in sync**:
- Python: `packages/textutils/normalize.py` (canonical) + `scripts/validate_data.py`
- TypeScript: `app/src/lib/greek/normalize.ts`
- SQL: `supabase/migrations/005_tei_first_schema.sql` (`normalize_greek_v1_1`)

Rules: lowercase → NFD → strip ALL combining marks U+0300–U+036F (including iota subscript U+0345) → NFC. Key test: `normalize("τῇ") == "τη"`.

See `docs/contracts/normalization_contract.md` for full specification.

### Vocab extraction tooling
`scripts/vocab_agent_runner.py` and `scripts/vocab_multi_agent_pilot.py` run LLM-based term extraction. Results in `outputs/vocab_entries_v3/`. Import via `scripts/import_vocab_v3.py`.

## Domain Conventions
- Sources: `GAL_SMT`, `GAL_ALIM`, `AET_LM`, `DIOSC_DMM`, `ORIB_CM`, `PAUL_RM`
- Legacy entry IDs: `SOURCE-ref` pattern (e.g. `GAL_SMT-6.1.1`)
- TEI-first entry IDs: `tei_doc_id~tei_segment_id` (e.g. `gal_smt~seg_6_1_1`)
- Lemma categories: `vegetable`, `animal`, `mineral`
- Translation status lifecycle: `draft` → `review` → `final`
- Assertion types: `quality` (HOT/COLD/DRY/WET with degrees), `part`, `process`, `other`
- CSVs use literal `\n` tokens for newlines within fields (not physical newlines)

## Environment
- Node.js 20+, Python 3.12+
- Root `.env.local` — `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (for import scripts)
- `app/.env.local` — `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (for Next.js)
- Python scripts use stdlib only (no pip dependencies) plus local `supabase_rest.py`; TEI indexer requires `lxml`
