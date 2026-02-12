# ancient-simples

## Project overview (plain English)
Ancient Simples is an internal scholarly database and web application for turning ancient Greek medical texts into a queryable, citable, cross-linked corpus. Researchers and editors should be able to answer questions like “where does ingredient X occur?”, “what preparations mention it?”, and “how is it described?” — with results that always include stable identifiers and complete references (logical refs like book/chapter/section and, where available, physical refs like edition volume/page/line).

The longer-term direction (see `docs/new_simples/`) is **TEI-first**: TEI is the read-only authority for Greek base text and citation structure, and the system projects TEI into Supabase/Postgres for fast querying while keeping editorial work (translations, lemma IDs/aliases, links, evidence-backed assertions) in SQL and exportable.
Start with `docs/new_simples/product_description.md` (plain-English product statement) and `docs/new_simples/new_wbs.md` (the working checklist).

### Aims
- Make cross-author retrieval and comparison tractable via stable lemma identity (and aliases for variants).
- Keep editorial work stable under base-text revision (drift is detectable and reviewable).
- Produce citable exports (structured datasets and, optionally, TEI standoff anchored to TEI IDs).

### Methods
- Single Next.js app backed by Supabase/Postgres/Auth; offline scripts allowed for validation, import/indexing, and exports.
- Deterministic IDs + strict, shared Greek normalization (Python/TypeScript/SQL must stay in sync).

### Outcomes
- Fast browsing/search and lemma-based comparison views grounded in citations.
- Structured exports for translations, links, and assertions that can be reused downstream.

## Current MVP constraints (this repo today)
- Next.js + Supabase only (no separate backend service).
- CSV-first pipeline (data restructuring produces importable CSVs).
- `lemma_ids` is import-only (used to populate `entry_lemmata`, not read by the app).

Workspace layout:
- `data-workbench/` — source spreadsheet + restructuring spec + CSV outputs.
- `docs/` — project specs (unchanged copies).
- `app/` — Next.js (App Router, TypeScript) MVP UI.

## Quick start (hosted Supabase)
Prereqs: Node.js 20+, Python 3.12+, Supabase CLI auth (`npx supabase login`).

1) Install tooling:
- `npm ci`
- `npm --prefix app ci`

2) Configure env (do not commit secrets):
- Copy `.env.example` → `.env.local` and fill `SUPABASE_SERVICE_ROLE_KEY` (required for import).
- Copy `app/.env.example` → `app/.env.local`.

3) Link + migrate the hosted project:
- `npm run supabase:link`
- `npm run db:push`

4) Validate CSVs + import into Supabase:
- `npm run data:validate`
- `npm run db:import`

5) Run the app:
- `npm --prefix app run dev`

## Verify Greek prefix search
In Supabase SQL editor:
```sql
select entry_id
from public.entries
where greek_normalized_prefix like 'αβρο%'
limit 5;
```

## Making an editor
New signups default to `viewer` via `public.profiles`.

In Supabase SQL editor:
```sql
select id, email from auth.users order by created_at desc limit 20;
update public.profiles set role = 'editor' where id = '<USER_ID_UUID>';
```

## CI / local checks
- `npm run ci`
