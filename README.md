# ancient-simples

MVP constraints:
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

## Making an editor
New signups default to `viewer` via `public.profiles`.

In Supabase SQL editor:
```sql
select id, email from auth.users order by created_at desc limit 20;
update public.profiles set role = 'editor' where id = '<USER_ID_UUID>';
```

## CI / local checks
- `npm run ci`
